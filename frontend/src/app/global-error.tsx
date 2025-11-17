"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Home } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log critical error to error reporting service
    console.error("Critical application error:", error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex min-h-screen items-center justify-center p-4 bg-background">
          <Card className="w-full max-w-md border-destructive">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-6 w-6 text-destructive" />
                <CardTitle className="text-destructive">Critical Error</CardTitle>
              </div>
              <CardDescription>
                A critical error occurred that prevented the application from functioning properly.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="rounded-lg bg-destructive/10 p-4 border border-destructive/20">
                  <p className="text-sm font-medium text-destructive">
                    {error.message || "An unknown critical error occurred"}
                  </p>
                  {error.digest && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Error ID: {error.digest}
                    </p>
                  )}
                </div>
                <div className="text-sm text-muted-foreground space-y-2">
                  <p>This error has been logged and our team has been notified.</p>
                  <p>You can try the following:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>Refresh the page</li>
                    <li>Clear your browser cache</li>
                    <li>Return to the homepage</li>
                  </ul>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-2">
              <Button
                onClick={reset}
                variant="default"
                className="w-full"
              >
                Retry
              </Button>
              <Button
                onClick={() => (window.location.href = "/")}
                variant="outline"
                className="w-full"
              >
                <Home className="mr-2 h-4 w-4" />
                Go to homepage
              </Button>
            </CardFooter>
          </Card>
        </div>
      </body>
    </html>
  );
}
