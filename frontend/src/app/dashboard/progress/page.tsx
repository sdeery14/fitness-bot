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

import { ProgressChart } from '@/components/fitness/progress-chart';

export default function ProgressPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
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
