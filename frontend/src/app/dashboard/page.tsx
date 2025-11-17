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

import { useRouter } from 'next/navigation';
import { DailySchedule } from '@/components/fitness/daily-schedule';
import { ProgressChart } from '@/components/fitness/progress-chart';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar, MessageSquare, TrendingUp, User } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">
          Track your progress and stay on schedule
        </p>
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
          <DailySchedule />
        </div>

        {/* Progress Overview */}
        <div>
          <ProgressChart />
        </div>
      </div>
    </div>
  );
}
