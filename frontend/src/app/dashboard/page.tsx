/**
 * Dashboard Home Page
 * 
 * Features:
 * - Welcome message with user info
 * - Today's schedule summary
 * - Quick actions (view schedule, track progress, chat)
 * - Recent progress overview
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { TodaySchedule } from '@/components/fitness/today-schedule';
import { ProgressChart } from '@/components/fitness/progress-chart';
import { DisruptionReportDialog } from '@/components/fitness/disruption-report-dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, MessageSquare, TrendingUp, User, AlertTriangle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function DashboardPage() {
  const router = useRouter();
  const [disruptionDialogOpen, setDisruptionDialogOpen] = useState(false);
  
  // TODO: Get actual fitness plan ID from user's active plan
  const fitnessPlanId = "placeholder-plan-id";

  const handleDisruptionReported = (result: any) => {
    // Refresh schedule and progress data
    // In a real implementation, this would trigger a data refetch
    console.log('Disruption reported:', result);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header with Report Disruption Button */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Track your progress and stay on schedule
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => setDisruptionDialogOpen(true)}
          className="gap-2"
        >
          <AlertTriangle className="h-4 w-4" />
          Report Disruption
        </Button>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/dashboard/schedule')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Calendar className="h-8 w-8 text-blue-500" />
              <div>
                <h3 className="font-semibold">Schedule</h3>
                <p className="text-sm text-muted-foreground">View calendar</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/dashboard/progress')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-green-500" />
              <div>
                <h3 className="font-semibold">Progress</h3>
                <p className="text-sm text-muted-foreground">Track metrics</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/dashboard/chat')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-8 w-8 text-purple-500" />
              <div>
                <h3 className="font-semibold">Chat</h3>
                <p className="text-sm text-muted-foreground">Talk to AI</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/dashboard/plan')}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <User className="h-8 w-8 text-orange-500" />
              <div>
                <h3 className="font-semibold">Plan</h3>
                <p className="text-sm text-muted-foreground">View details</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Today's Schedule */}
        <div>
          <TodaySchedule />
        </div>

        {/* Progress Overview */}
        <div>
          <ProgressChart />
        </div>
      </div>

      {/* Disruption Report Dialog */}
      <DisruptionReportDialog
        open={disruptionDialogOpen}
        onOpenChange={setDisruptionDialogOpen}
        fitnessPlanId={fitnessPlanId}
        onDisruptionReported={handleDisruptionReported}
      />
    </div>
  );
}
