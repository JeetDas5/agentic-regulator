import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const maxDuration = 60; // Next.js edge/serverless function max duration

// The desired JSON Schema structure for OpenAI
const ResponseSchema = {
  name: "RegulatoryResponse",
  schema: {
    type: "object",
    properties: {
      regulation_id: { type: "string" },
      source: {
        type: "object",
        properties: {
          organization: { type: "string" },
          url: { type: "string" },
          published_date: { type: "string" },
          document_type: { type: "string" },
        },
        required: ["organization", "url", "published_date", "document_type"],
        additionalProperties: false
      },
      document_metadata: {
        type: "object",
        properties: {
          title: { type: "string" },
          reference_number: { type: "string" },
          category: { type: "string" },
          language: { type: "string" },
          pages: { type: "integer" },
        },
        required: ["title", "reference_number", "category", "language", "pages"],
        additionalProperties: false
      },
      summary: {
        type: "object",
        properties: {
          short_summary: { type: "string" },
          detailed_summary: { type: "string" },
        },
        required: ["short_summary", "detailed_summary"],
        additionalProperties: false
      },
      risk_assessment: {
        type: "object",
        properties: {
          severity: { type: "string" },
          priority_score: { type: "integer" },
          reasoning: { type: "array", items: { type: "string" } },
        },
        required: ["severity", "priority_score", "reasoning"],
        additionalProperties: false
      },
      compliance_requirements: {
        type: "array",
        items: {
          type: "object",
          properties: {
            requirement_id: { type: "string" },
            requirement: { type: "string" },
            mandatory: { type: "boolean" },
            deadline: { type: "string" },
            affected_entities: { type: "array", items: { type: "string" } },
          },
          required: ["requirement_id", "requirement", "mandatory", "deadline", "affected_entities"],
          additionalProperties: false
        }
      },
      impacted_departments: {
        type: "array",
        items: {
          type: "object",
          properties: {
            department: { type: "string" },
            reason: { type: "string" },
          },
          required: ["department", "reason"],
          additionalProperties: false
        }
      },
      maps: {
        type: "array",
        items: {
          type: "object",
          properties: {
            map_id: { type: "string" },
            title: { type: "string" },
            description: { type: "string" },
            department: { type: "string" },
            priority: { type: "string" },
            deadline: { type: "string" },
            status: { type: "string" },
            validation_method: { type: "array", items: { type: "string" } },
            required_evidence: { type: "array", items: { type: "string" } },
          },
          required: ["map_id", "title", "description", "department", "priority", "deadline", "status", "validation_method", "required_evidence"],
          additionalProperties: false
        }
      },
      validation_rules: {
        type: "array",
        items: {
          type: "object",
          properties: {
            rule_id: { type: "string" },
            rule: { type: "string" },
            validation_type: { type: "string" },
            success_criteria: { type: "string" },
          },
          required: ["rule_id", "rule", "validation_type", "success_criteria"],
          additionalProperties: false
        }
      },
      audit_trail: {
        type: "object",
        properties: {
          confidence_score: { type: "number" },
          human_review_required: { type: "boolean" },
        },
        required: ["confidence_score", "human_review_required"],
        additionalProperties: false
      }
    },
    required: [
      "regulation_id",
      "source",
      "document_metadata",
      "summary",
      "risk_assessment",
      "compliance_requirements",
      "impacted_departments",
      "maps",
      "validation_rules",
      "audit_trail"
    ],
    additionalProperties: false
  },
  strict: true
};

export async function POST(req) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // 1. Send the file to Python Parser
    const parserFormData = new FormData();
    parserFormData.append("files", file);
    parserFormData.append("section", "full");

    const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
    const parserResponse = await fetch(`${pythonApiUrl}/api/v1/parse`, {
      method: "POST",
      body: parserFormData,
    });

    if (!parserResponse.ok) {
      const errorText = await parserResponse.text();
      throw new Error(`Python Parser failed: ${errorText}`);
    }

    const parserData = await parserResponse.json();
    if (!parserData.results || parserData.results.length === 0 || parserData.results[0].status === "error") {
      throw new Error("Python parser returned an error for the file.");
    }

    const extractedContent = parserData.results[0].data.content.full_text || parserData.results[0].data.content.clean_text;
    
    if (!extractedContent) {
      throw new Error("Failed to extract text content from the PDF.");
    }

    // 2. Pass extracted text to OpenAI for structured parsing
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: "You are a Regulatory Compliance Expert. Analyze the following regulatory document (from RBI or similar). Extract and structure all relevant Measurable Action Points (MAPs), compliance requirements, impacted departments, and risk assessment into the requested JSON schema. Be highly analytical and precise."
        },
        {
          role: "user",
          content: `Here is the extracted text from the regulatory PDF:\n\n${extractedContent.substring(0, 30000)}` // Limit text to fit context window comfortably
        }
      ],
      response_format: {
        type: "json_schema",
        json_schema: ResponseSchema
      }
    });

    const llmOutput = JSON.parse(completion.choices[0].message.content);

    // 3. Save to Prisma Postgres
    const savedDoc = await prisma.regulatoryDocument.create({
      data: {
        regulation_id: llmOutput.regulation_id,
        organization: llmOutput.source.organization,
        url: llmOutput.source.url,
        published_date: llmOutput.source.published_date,
        document_type: llmOutput.source.document_type,
        
        title: llmOutput.document_metadata.title,
        reference_number: llmOutput.document_metadata.reference_number,
        category: llmOutput.document_metadata.category,
        language: llmOutput.document_metadata.language,
        pages: llmOutput.document_metadata.pages,
        
        short_summary: llmOutput.summary.short_summary,
        detailed_summary: llmOutput.summary.detailed_summary,
        
        risk_severity: llmOutput.risk_assessment.severity,
        risk_priority_score: llmOutput.risk_assessment.priority_score,
        risk_reasoning: llmOutput.risk_assessment.reasoning,
        
        processed_at: new Date(),
        llm_model: "gpt-4o-mini",
        confidence_score: llmOutput.audit_trail.confidence_score,
        human_review_required: llmOutput.audit_trail.human_review_required,

        compliance_requirements: {
          create: llmOutput.compliance_requirements.map((req) => ({
            requirement_id: req.requirement_id,
            requirement: req.requirement,
            mandatory: req.mandatory,
            deadline: req.deadline,
            affected_entities: req.affected_entities,
          }))
        },
        impacted_departments: {
          create: llmOutput.impacted_departments.map((dept) => ({
            department: dept.department,
            reason: dept.reason,
          }))
        },
        maps: {
          create: llmOutput.maps.map((map) => ({
            map_id: map.map_id,
            title: map.title,
            description: map.description,
            department: map.department,
            priority: map.priority,
            deadline: map.deadline,
            status: map.status,
            validation_method: map.validation_method,
            required_evidence: map.required_evidence,
          }))
        },
        validation_rules: {
          create: llmOutput.validation_rules.map((rule) => ({
            rule_id: rule.rule_id,
            rule: rule.rule,
            validation_type: rule.validation_type,
            success_criteria: rule.success_criteria,
          }))
        }
      }
    });

    return NextResponse.json({ success: true, documentId: savedDoc.id, data: savedDoc });

  } catch (error) {
    console.error("Processing error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
