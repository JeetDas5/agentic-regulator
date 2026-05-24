import Link from "next/link";
import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ExternalLink, ShieldAlert, Calendar, CheckSquare } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default async function DocumentDetail({ params }) {
  const { id } = await params;

  const doc = await prisma.regulatoryDocument.findUnique({
    where: { id },
    include: {
      compliance_requirements: true,
      impacted_departments: true,
      maps: true,
      validation_rules: true,
    }
  });

  if (!doc) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        <Link href="/dashboard" className="text-slate-500 hover:text-slate-900 flex items-center text-sm font-medium">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Dashboard
        </Link>

        {/* Header section */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Badge variant="outline" className="bg-white">{doc.regulation_id}</Badge>
              <Badge variant={doc.risk_severity.toLowerCase() === 'high' ? 'destructive' : 'secondary'}>
                {doc.risk_severity} Risk (Score: {doc.risk_priority_score})
              </Badge>
            </div>
            <h1 className="text-3xl font-bold text-slate-900">{doc.title}</h1>
            <p className="text-slate-600 mt-2 max-w-3xl">{doc.detailed_summary}</p>
          </div>
          <div className="flex-shrink-0">
            <a 
              href={doc.url} 
              target="_blank" 
              rel="noreferrer"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
            >
              Original Source <ExternalLink className="ml-2 w-4 h-4" />
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Left Column: Metadata & Departments */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">Organization</p>
                  <p className="text-sm">{doc.organization}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Published Date</p>
                  <p className="text-sm">{doc.published_date}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Category</p>
                  <p className="text-sm">{doc.category}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-500">Reference No</p>
                  <p className="text-sm">{doc.reference_number}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Impacted Departments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {doc.impacted_departments.map(dept => (
                  <div key={dept.id} className="border-l-2 border-blue-500 pl-3">
                    <p className="font-semibold text-slate-900">{dept.department}</p>
                    <p className="text-sm text-slate-600 mt-1">{dept.reason}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: MAPs & Requirements */}
          <div className="md:col-span-2 space-y-6">
            
            {/* Measurable Action Points */}
            <Card>
              <CardHeader>
                <CardTitle className="text-xl flex items-center">
                  <CheckSquare className="mr-2 h-5 w-5 text-blue-600" />
                  Measurable Action Points (MAPs)
                </CardTitle>
                <CardDescription>
                  Tasks extracted by AI, assigned to specific departments for execution.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {doc.maps.map(map => (
                    <div key={map.id} className="p-4 rounded-lg border border-slate-200 bg-white">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-semibold text-lg text-slate-900">{map.title}</h3>
                          <p className="text-sm text-slate-600 mt-1">{map.description}</p>
                        </div>
                        <Badge variant={map.priority.toLowerCase() === 'critical' ? 'destructive' : 'secondary'}>
                          {map.priority}
                        </Badge>
                      </div>
                      
                      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-slate-500 block">Assigned To</span>
                          <span className="inline-flex items-center mt-1 bg-slate-100 px-2 py-1 rounded text-slate-800">
                            {map.department}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-slate-500 block">Deadline</span>
                          <span className="inline-flex items-center mt-1 text-slate-800">
                            <Calendar className="w-4 h-4 mr-1 text-slate-400" />
                            {map.deadline}
                          </span>
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <span className="font-medium text-sm text-slate-500 mb-2 block">Validation Methods:</span>
                        <ul className="list-disc list-inside text-sm text-slate-700 space-y-1">
                          {map.validation_method.map((method, idx) => (
                            <li key={idx}>{method}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Validation Rules */}
            <Card>
              <CardHeader>
                <CardTitle className="text-xl flex items-center">
                  <ShieldAlert className="mr-2 h-5 w-5 text-green-600" />
                  Validation Rules
                </CardTitle>
                <CardDescription>
                  Rules the Validation Agent uses to verify compliance.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rule</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Success Criteria</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {doc.validation_rules.map(rule => (
                      <TableRow key={rule.id}>
                        <TableCell className="font-medium">{rule.rule}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{rule.validation_type}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-600">{rule.success_criteria}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

          </div>
        </div>

      </div>
    </div>
  );
}
