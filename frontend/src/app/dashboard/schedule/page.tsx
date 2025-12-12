/**
 * Schedule Page - Full calendar view of workouts and meals
 * 
 * Features:
 * - 14-day calendar view
 * - Daily schedule details
 * - Filter by activity type
 * - Navigation controls
 */

'use client';

import { useRouter } from 'next/navigation';
import { ScheduleCalendar } from '@/components/fitness/schedule-calendar';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function SchedulePage() {
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
        <h1 className="text-3xl font-bold mb-2">Schedule</h1>
        <p className="text-muted-foreground">
          View and manage your workout and meal schedule
        </p>
      </div>

      {/* Calendar View */}
      <ScheduleCalendar />
    </div>
  );
}
