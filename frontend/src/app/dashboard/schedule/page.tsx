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
import { DailySchedule } from '@/components/fitness/daily-schedule';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

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

      {/* Tabs */}
      <Tabs defaultValue="calendar" className="space-y-6">
        <TabsList>
          <TabsTrigger value="calendar">Calendar View</TabsTrigger>
          <TabsTrigger value="today">Today</TabsTrigger>
        </TabsList>

        <TabsContent value="calendar" className="space-y-6">
          <ScheduleCalendar />
        </TabsContent>

        <TabsContent value="today">
          <DailySchedule />
        </TabsContent>
      </Tabs>
    </div>
  );
}
