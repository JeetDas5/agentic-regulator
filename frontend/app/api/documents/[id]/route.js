import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req, { params }) {
  try {
    const documentId = params.id;

    const document = await prisma.regulatoryDocument.findUnique({
      where: { id: documentId },
      include: {
        compliance_requirements: true,
        impacted_departments: true,
        maps: true,
        validation_rules: true,
      }
    });

    if (!document) {
      return NextResponse.json({ error: "Document not found" }, { status: 404 });
    }

    return NextResponse.json(document);
  } catch (error) {
    console.error("Error fetching document:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
