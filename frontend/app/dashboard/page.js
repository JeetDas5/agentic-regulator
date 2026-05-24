import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const documents = await prisma.regulatoryDocument.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      maps: true,
      impacted_departments: true,
    }
  });

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Regulatory Dashboard</h1>
            <p className="text-slate-600 mt-1">Overview of processed regulatory documents and assignments.</p>
          </div>
          <Link href="/">
            <Button>Upload New Document</Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Processed</CardDescription>
              <CardTitle className="text-4xl">{documents.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Action Points (MAPs)</CardDescription>
              <CardTitle className="text-4xl">
                {documents.reduce((acc, doc) => acc + doc.maps.length, 0)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Critical Tasks</CardDescription>
              <CardTitle className="text-4xl text-red-600">
                {documents.reduce((acc, doc) => acc + doc.maps.filter(m => m.priority.toLowerCase() === 'critical').length, 0)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
          </CardHeader>
          <CardContent>
            {documents.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <FileText className="mx-auto h-12 w-12 text-slate-300 mb-3" />
                <p>No documents processed yet.</p>
                <Link href="/" className="text-blue-600 hover:underline mt-2 inline-block">
                  Upload your first document
                </Link>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Regulation ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Risk</TableHead>
                    <TableHead>Departments</TableHead>
                    <TableHead>Date Processed</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">{doc.regulation_id}</TableCell>
                      <TableCell className="max-w-xs truncate" title={doc.title}>{doc.title}</TableCell>
                      <TableCell>
                        <Badge variant={doc.risk_severity.toLowerCase() === 'high' ? 'destructive' : 'secondary'}>
                          {doc.risk_severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {doc.impacted_departments.map(d => (
                            <Badge key={d.id} variant="outline" className="text-xs">
                              {d.department}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{new Date(doc.createdAt).toLocaleDateString()}</TableCell>
                      <TableCell className="text-right">
                        <Link href={`/dashboard/${doc.id}`}>
                          <Button variant="ghost" size="sm">
                            View <ArrowRight className="ml-2 h-4 w-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
