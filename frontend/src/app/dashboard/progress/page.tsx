/**
 * Progress Page - Detailed progress tracking and measurements
 * 
 * Features:
 * - Progress charts and trends
 * - Measurement history
 * - Add new measurements
 * - Adherence statistics
 */

'use client';

import { useRouter } from 'next/navigation';
import { ProgressChart } from '@/components/fitness/progress-chart';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function ProgressPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <Button
          variant="ghost"
          onClick={() => router.push('/dashboard')}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
        <h1 className="text-3xl font-bold mb-2">Progress Tracking</h1>
        <p className="text-muted-foreground">
          Monitor your adherence, measurements, and overall progress
        </p>
      </div>

      {/* Progress Content */}
      <ProgressChart />
    </div>
  );
}
