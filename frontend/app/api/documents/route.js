import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const documents = await prisma.regulatoryDocument.findMany({
      orderBy: { createdAt: 'desc' },
      include: {
        impacted_departments: true,
        maps: true,
      }
    });

    return NextResponse.json(documents);
  } catch (error) {
    console.error("Error fetching documents:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
