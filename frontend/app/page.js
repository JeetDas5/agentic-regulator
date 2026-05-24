"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle"); // idle, uploading, parsing, done, error
  const [errorMsg, setErrorMsg] = useState("");
  const router = useRouter();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("idle");
      setErrorMsg("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setStatus("uploading");
    setProgress(10);

    const formData = new FormData();
    formData.append("file", file);

    try {
      setProgress(40);
      setStatus("parsing");

      const res = await fetch("/api/process", {
        method: "POST",
        body: formData,
      });

      setProgress(80);

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Failed to process document");
      }

      setProgress(100);
      setStatus("done");

      // Redirect to the newly created document dashboard
      setTimeout(() => {
        router.push(`/dashboard/${data.documentId}`);
      }, 1000);

    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
      setStatus("error");
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl w-full text-center mb-8">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl mb-4">
          Agentic Regulatory Intelligence
        </h1>
        <p className="text-lg text-slate-600">
          Upload regulatory documents to autonomously extract Measurable Action Points (MAPs), 
          assign departments, and generate compliance validation rules using AI.
        </p>
      </div>

      <Card className="w-full max-w-xl shadow-lg border-slate-200">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Analyze Document</CardTitle>
          <CardDescription>Upload an RBI circular or notification (PDF) to begin.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-6">
          
          {/* Upload Area */}
          <div className="w-full border-2 border-dashed border-slate-300 rounded-lg p-10 flex flex-col items-center justify-center bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer relative">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={isUploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            {file ? (
              <>
                <FileText className="w-12 h-12 text-blue-600 mb-4" />
                <p className="text-sm font-medium text-slate-700">{file.name}</p>
                <p className="text-xs text-slate-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </>
            ) : (
              <>
                <Upload className="w-12 h-12 text-slate-400 mb-4" />
                <p className="text-sm font-medium text-slate-700">Click to upload or drag and drop</p>
                <p className="text-xs text-slate-500 mt-1">PDF up to 50MB</p>
              </>
            )}
          </div>

          {/* Progress and Status */}
          {status !== "idle" && (
            <div className="w-full space-y-2">
              <div className="flex justify-between text-sm font-medium text-slate-700">
                <span>
                  {status === "uploading" && "Uploading document..."}
                  {status === "parsing" && "AI is extracting and structuring data (this may take up to a minute)..."}
                  {status === "done" && "Processing complete! Redirecting..."}
                  {status === "error" && "Error processing document"}
                </span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Error Message */}
          {status === "error" && (
            <div className="w-full p-4 bg-red-50 border border-red-200 rounded-md flex items-start text-red-700 text-sm">
              <AlertCircle className="w-5 h-5 mr-2 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Action Button */}
          <Button
            className="w-full"
            size="lg"
            onClick={handleUpload}
            disabled={!file || isUploading}
          >
            {isUploading ? (
              "Processing..."
            ) : (
              <>
                Extract Insights <CheckCircle className="ml-2 w-4 h-4" />
              </>
            )}
          </Button>

          <Button variant="link" onClick={() => router.push('/dashboard')} className="text-slate-500">
            View existing processed documents
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
