/**
 * Schedule Page - Full calendar view of workouts and meals
 * 
 * Features:
 * - Monthly calendar view (7 days past + 30 days ahead)
 * - Daily schedule details
 * - Filter by activity type
 * - Navigation controls
 */

'use client';

import { ScheduleCalendar } from '@/components/fitness/schedule-calendar';

export default function SchedulePage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
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
