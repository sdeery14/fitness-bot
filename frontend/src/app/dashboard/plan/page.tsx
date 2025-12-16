"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PhaseTimeline } from "@/components/fitness/phase-timeline";
import { MilestoneCelebration } from "@/components/fitness/milestone-celebration";
import {
  ArrowLeft,
  Calendar,
  Target,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
  Pause,
  Play,
  ShoppingCart,
  ChefHat,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Phase {
  id: string;
  phase_number: number;
  name: string;
  objectives: string[];
  start_date: string;
  end_date: string;
  phase_details: any;
}

interface FitnessPlan {
  id: string;
  user_id: string;
  goal_description: string;
  goal_type: string;
  duration_weeks: number;
  start_date: string;
  target_end_date: string;
  current_status: string;
  phases: any[];
  workout_frequency: number;
  daily_calorie_target: number;
  created_at: string;
  updated_at: string;
  key_principles?: string[];
  success_metrics?: string[];
  important_notes?: string;
  workout_metadata?: {
    phase_progression_notes?: string;
    equipment_used?: string[];
  };
  meal_metadata?: {
    dietary_approach?: string;
    macro_strategy?: string;
    meal_timing?: string;
    hydration_guidance?: string;
    phase_nutrition_notes?: string;
  };
}

interface ScheduleStatistics {
  total_entries: number;
  completed: number;
  scheduled: number;
  skipped: number;
  total_workouts: number;
  total_meals: number;
  completion_rate: number;
}

interface ScheduleData {
  schedule_id: string;
  start_date: string;
  last_recalculated_at: string;
  statistics: ScheduleStatistics;
  upcoming_entries: any[];
}

interface PhaseStatus {
  has_phases: boolean;
  current_phase: {
    id: string;
    phase_number: number;
    name: string;
    objectives: string[];
    start_date: string;
    end_date: string;
    days_remaining: number;
  } | null;
  next_phase: {
    id: string;
    phase_number: number;
    name: string;
    objectives: string[];
    start_date: string;
    end_date: string;
  } | null;
  is_complete: boolean;
  should_transition: boolean;
  all_phases_complete?: boolean;
}

export default function PlanPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [allPlans, setAllPlans] = useState<FitnessPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<FitnessPlan | null>(null);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [phaseStatus, setPhaseStatus] = useState<PhaseStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showMilestone, setShowMilestone] = useState(false);
  const [currentMilestone, setCurrentMilestone] = useState<any>(null);
  const [activatingPlanId, setActivatingPlanId] = useState<string | null>(null);
  const [showActivateDialog, setShowActivateDialog] = useState(false);
  const [planToActivate, setPlanToActivate] = useState<FitnessPlan | null>(null);
  const [scheduleData, setScheduleData] = useState<ScheduleData | null>(null);
  const [loadingSchedule, setLoadingSchedule] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setAccessToken(token);
      fetchAllPlans(token);
    }
  }, [router]);

  const fetchAllPlans = async (token: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch all plans
      const plansRes = await fetch(`${API_URL}/fitness-plans`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!plansRes.ok) {
        throw new Error("Failed to load fitness plans");
      }

      const plansData = await plansRes.json();
      const plans = plansData.data?.plans || [];
      setAllPlans(plans);

      // Select the active plan by default, or the most recent plan
      const activePlan = plans.find((p: FitnessPlan) => p.current_status === "active");
      const planToSelect = activePlan || plans[0] || null;
      
      if (planToSelect) {
        selectPlan(planToSelect, token);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plans");
      console.error("Error fetching plans:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchScheduleData = async (planId: string, token: string) => {
    try {
      setLoadingSchedule(true);
      const response = await fetch(`${API_URL}/schedules/plan/${planId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setScheduleData(data.data);
      } else {
        setScheduleData(null);
      }
    } catch (err) {
      console.error("Error fetching schedule:", err);
      setScheduleData(null);
    } finally {
      setLoadingSchedule(false);
    }
  };

  const selectPlan = async (plan: FitnessPlan, token?: string) => {
    // Set basic plan data immediately
    setSelectedPlan(plan);

    const authToken = token || accessToken;
    if (!authToken) return;

    try {
      // Fetch full plan details with all metadata
      const detailsRes = await fetch(`${API_URL}/fitness-plans/${plan.id}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (detailsRes.ok) {
        const detailsData = await detailsRes.json();
        const fullPlan = detailsData.data;
        console.log('Full plan data fetched:', fullPlan);
        setSelectedPlan(fullPlan);

        // Extract phases from full plan data
        if (fullPlan.phases) {
          setPhases(fullPlan.phases);
        } else {
          setPhases([]);
        }

        // Derive phase status from full plan data
        if (fullPlan.phases) {
          const today = new Date();
          const currentPhase = fullPlan.phases.find((p: Phase) => {
            const start = new Date(p.start_date);
            const end = new Date(p.end_date);
            return start <= today && today <= end;
          });

          if (currentPhase) {
            const endDate = new Date(currentPhase.end_date);
            const daysRemaining = Math.ceil(
              (endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
            );

            const currentIndex = fullPlan.phases.findIndex(
              (p: Phase) => p.id === currentPhase.id
            );
            const nextPhase =
              currentIndex < fullPlan.phases.length - 1
                ? fullPlan.phases[currentIndex + 1]
                : null;

            setPhaseStatus({
              has_phases: true,
              current_phase: {
                ...currentPhase,
                days_remaining: daysRemaining,
              },
              next_phase: nextPhase,
              is_complete: daysRemaining <= 2,
              should_transition: daysRemaining <= 2 && nextPhase !== null,
            });
          } else {
            setPhaseStatus(null);
          }
        } else {
          setPhaseStatus(null);
        }
      } else {
        console.error('Failed to fetch plan details:', detailsRes.status, detailsRes.statusText);
        const errorText = await detailsRes.text();
        console.error('Error response:', errorText);
      }
    } catch (err) {
      console.error("Error fetching plan details:", err);
      setError(err instanceof Error ? err.message : "Failed to load plan details");
    }

    // Fetch schedule data for this plan
    fetchScheduleData(plan.id, authToken);
  };

  const handleActivatePlan = async (plan: FitnessPlan) => {
    if (!accessToken) return;

    // Check if there's already an active plan
    const hasActivePlan = allPlans.some(
      (p) => p.current_status === "active" && p.id !== plan.id
    );

    if (hasActivePlan) {
      setPlanToActivate(plan);
      setShowActivateDialog(true);
    } else {
      await activatePlan(plan.id);
    }
  };

  const activatePlan = async (planId: string) => {
    if (!accessToken) return;

    try {
      setActivatingPlanId(planId);

      // First, deactivate all other plans
      const activePlans = allPlans.filter((p) => p.current_status === "active");
      for (const activePlan of activePlans) {
        await fetch(`${API_URL}/fitness-plans/${activePlan.id}`, {
          method: "PATCH",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ current_status: "paused" }),
        });
      }

      // Activate the selected plan
      const response = await fetch(`${API_URL}/fitness-plans/${planId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ current_status: "active" }),
      });

      if (!response.ok) {
        throw new Error("Failed to activate plan");
      }

      // Refresh plans
      await fetchAllPlans(accessToken);
    } catch (err) {
      console.error("Error activating plan:", err);
      setError(err instanceof Error ? err.message : "Failed to activate plan");
    } finally {
      setActivatingPlanId(null);
      setShowActivateDialog(false);
      setPlanToActivate(null);
    }
  };

  const handlePausePlan = async (planId: string) => {
    if (!accessToken) return;

    try {
      const response = await fetch(`${API_URL}/fitness-plans/${planId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ current_status: "paused" }),
      });

      if (!response.ok) {
        throw new Error("Failed to pause plan");
      }

      // Refresh plans
      await fetchAllPlans(accessToken);
    } catch (err) {
      console.error("Error pausing plan:", err);
      setError(err instanceof Error ? err.message : "Failed to pause plan");
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading your fitness plan...</p>
        </div>
      </div>
    );
  }

  if (error && allPlans.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error || "No fitness plans found"}</p>
          <Button onClick={() => router.push("/dashboard")}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return <Badge className="bg-green-600 hover:bg-green-700">Active</Badge>;
      case "paused":
        return <Badge variant="secondary">Paused</Badge>;
      case "completed":
        return <Badge className="bg-blue-600 hover:bg-blue-700">Completed</Badge>;
      case "draft":
        return <Badge variant="outline">Draft</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/dashboard")}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-xl font-semibold text-gray-900">
                My Fitness Plans
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Plan List Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">All Plans</CardTitle>
                <CardDescription>
                  {allPlans.length} {allPlans.length === 1 ? "plan" : "plans"} created
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {allPlans.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p className="text-sm">No plans found</p>
                    <Button
                      variant="link"
                      onClick={() => router.push("/dashboard")}
                      className="mt-2"
                    >
                      Create your first plan
                    </Button>
                  </div>
                ) : (
                  allPlans.map((plan) => (
                    <div
                      key={plan.id}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        selectedPlan?.id === plan.id
                          ? "border-blue-600 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300 bg-white"
                      }`}
                      onClick={() => selectPlan(plan)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-sm text-gray-900 line-clamp-2">
                          {plan.goal_description}
                        </h3>
                        {getStatusBadge(plan.current_status)}
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div className="flex items-center gap-1">
                          <Target className="h-3 w-3" />
                          <span>{plan.goal_type.replace(/_/g, " ")}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(plan.start_date)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{plan.duration_weeks} weeks</span>
                        </div>
                      </div>
                      <div className="mt-3 flex gap-2">
                        {plan.current_status === "active" ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePausePlan(plan.id);
                            }}
                            className="flex-1 text-xs"
                          >
                            <Pause className="h-3 w-3 mr-1" />
                            Pause
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="default"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleActivatePlan(plan);
                            }}
                            disabled={activatingPlanId === plan.id}
                            className="flex-1 text-xs"
                          >
                            <Play className="h-3 w-3 mr-1" />
                            {activatingPlanId === plan.id ? "Activating..." : "Activate"}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Plan Details */}
          <div className="lg:col-span-2">
            {!selectedPlan ? (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center text-gray-500">
                    <Target className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p>Select a plan to view details</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Combined Plan Details */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Target className="h-5 w-5 text-blue-600" />
                        <CardTitle>Plan Details</CardTitle>
                      </div>
                      {getStatusBadge(selectedPlan.current_status)}
                    </div>
                    <CardDescription>
                      Complete overview of your fitness plan and progress
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Goal Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        {selectedPlan.goal_description}
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-gray-500 uppercase">Goal Type</span>
                          <span className="text-sm font-medium text-gray-900">
                            {selectedPlan.goal_type.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-gray-500 uppercase">Started</span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatDate(selectedPlan.start_date)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-gray-500 uppercase">Target Date</span>
                          <span className="text-sm font-medium text-gray-900">
                            {formatDate(selectedPlan.target_end_date)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <span className="text-xs text-gray-500 uppercase">Duration</span>
                          <span className="text-sm font-medium text-gray-900">
                            {selectedPlan.duration_weeks} weeks
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Schedule Statistics */}
                    {scheduleData && scheduleData.statistics && (
                      <div className="border-t pt-6">
                        <h4 className="font-semibold text-gray-900 mb-4">Schedule Progress</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                            <div className="text-2xl font-bold text-green-700">
                              {scheduleData.statistics.completion_rate}%
                            </div>
                            <div className="text-xs text-green-600 uppercase mt-1">
                              Completion Rate
                            </div>
                          </div>
                          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                            <div className="text-2xl font-bold text-blue-700">
                              {scheduleData.statistics.completed}
                            </div>
                            <div className="text-xs text-blue-600 uppercase mt-1">
                              Completed
                            </div>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                            <div className="text-2xl font-bold text-gray-700">
                              {scheduleData.statistics.scheduled}
                            </div>
                            <div className="text-xs text-gray-600 uppercase mt-1">
                              Scheduled
                            </div>
                          </div>
                          <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                            <div className="text-2xl font-bold text-orange-700">
                              {scheduleData.statistics.skipped}
                            </div>
                            <div className="text-xs text-orange-600 uppercase mt-1">
                              Skipped
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-4 text-sm text-gray-600">
                          <span>
                            <strong>{scheduleData.statistics.total_workouts}</strong> Total Workouts
                          </span>
                          <span>•</span>
                          <span>
                            <strong>{scheduleData.statistics.total_meals}</strong> Total Meals
                          </span>
                          <span>•</span>
                          <span>
                            <strong>{scheduleData.statistics.total_entries}</strong> Total Entries
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Current Phase */}
                    {phaseStatus && phaseStatus.current_phase && (
                      <div className="border-t pt-6">
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-blue-900">
                              Current Phase: {phaseStatus.current_phase.name}
                            </h4>
                            <Badge variant="outline" className="bg-white">
                              Phase {phaseStatus.current_phase.phase_number}
                            </Badge>
                          </div>
                          <p className="text-sm text-blue-700 mb-3">
                            {phaseStatus.current_phase.days_remaining} days remaining
                          </p>
                          <div>
                            <p className="text-xs font-semibold text-blue-900 mb-2 uppercase">
                              Phase Objectives:
                            </p>
                            <ul className="space-y-1">
                              {phaseStatus.current_phase.objectives.map((obj: string, idx: number) => (
                                <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                                  <TrendingUp className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                  <span>{obj}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Plan Metadata */}
                    <div className="border-t pt-6">
                      <h4 className="font-semibold text-gray-900 mb-4">Plan Overview</h4>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Training Overview */}
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 space-y-3">
                          <h5 className="font-semibold text-blue-900 flex items-center gap-2">
                            <TrendingUp className="h-4 w-4" />
                            Training Strategy
                          </h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-blue-700">Workout Frequency:</span>
                              <span className="font-medium text-blue-900">{selectedPlan.workout_frequency || 3} days/week</span>
                            </div>
                            {selectedPlan.workout_metadata?.equipment_used && selectedPlan.workout_metadata.equipment_used.length > 0 && (
                              <div>
                                <span className="text-blue-700">Equipment:</span>
                                <p className="text-blue-900 mt-1">{selectedPlan.workout_metadata.equipment_used.join(', ')}</p>
                              </div>
                            )}
                            {selectedPlan.workout_metadata?.phase_progression_notes && (
                              <div>
                                <span className="text-blue-700">Progression:</span>
                                <p className="text-blue-900 mt-1">{selectedPlan.workout_metadata.phase_progression_notes}</p>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Nutrition Overview */}
                        <div className="p-4 bg-green-50 rounded-lg border border-green-200 space-y-3">
                          <h5 className="font-semibold text-green-900 flex items-center gap-2">
                            <Target className="h-4 w-4" />
                            Nutrition Strategy
                          </h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-green-700">Approach:</span>
                              <span className="font-medium text-green-900">{selectedPlan.meal_metadata?.dietary_approach || 'Balanced'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-green-700">Macro Strategy:</span>
                              <span className="font-medium text-green-900">{selectedPlan.meal_metadata?.macro_strategy || 'Balanced'}</span>
                            </div>
                            {selectedPlan.meal_metadata?.meal_timing && (
                              <div className="flex justify-between">
                                <span className="text-green-700">Meal Timing:</span>
                                <span className="font-medium text-green-900">{selectedPlan.meal_metadata.meal_timing}</span>
                              </div>
                            )}
                            {selectedPlan.meal_metadata?.hydration_guidance && (
                              <div>
                                <span className="text-green-700">Hydration:</span>
                                <p className="text-green-900 mt-1">{selectedPlan.meal_metadata.hydration_guidance}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Phase Details */}
                    {selectedPlan.phases && (
                      <div className="border-t pt-6">
                        <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                          <Calendar className="h-5 w-5 text-purple-600" />
                          Phase Details
                        </h4>
                        <div className="space-y-4">
                          {selectedPlan.phases && selectedPlan.phases.length > 0 && (
                            <div>
                              <div className="space-y-4">
                                {selectedPlan.phases.map((phase: any, idx: number) => (
                                  <details key={idx} className="group" open={idx === 0}>
                                    <summary className="p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border-2 border-gray-200 cursor-pointer hover:border-gray-300 transition-all">
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          <div className="flex items-center gap-2 mb-2">
                                            <Badge className="bg-gradient-to-r from-blue-600 to-green-600">
                                              Phase {phase.phase_number}
                                            </Badge>
                                            <h6 className="font-semibold text-gray-900">{phase.name}</h6>
                                          </div>
                                          <p className="text-sm text-gray-700 mb-2">
                                            {formatDate(phase.start_date)} → {formatDate(phase.end_date)} 
                                            <span className="text-gray-500 ml-2">({phase.duration_weeks} weeks)</span>
                                          </p>
                                          {phase.objectives && phase.objectives.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-2">
                                              {phase.objectives.map((obj: string, objIdx: number) => (
                                                <Badge key={objIdx} variant="outline" className="text-xs">
                                                  {obj}
                                                </Badge>
                                              ))}
                                            </div>
                                          )}
                                        </div>
                                        <CheckCircle2 className="h-5 w-5 text-gray-400 group-open:rotate-90 transition-transform flex-shrink-0 ml-4" />
                                      </div>
                                    </summary>
                                    
                                    <div className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
                                      {/* Training Details Column */}
                                      <div className="p-4 bg-white rounded-lg border border-gray-200 space-y-4">
                                        <h6 className="font-semibold text-blue-900 flex items-center gap-2 pb-2 border-b">
                                          <TrendingUp className="h-4 w-4" />
                                          Training Plan
                                        </h6>
                                        {phase.workout_details && (
                                          <>
                                            {phase.workout_details.intensity_guidance && (
                                              <div className="p-3 bg-blue-50 rounded-lg">
                                                <p className="text-xs font-semibold text-blue-700 uppercase mb-1">Intensity</p>
                                                <p className="text-sm text-blue-900">{phase.workout_details.intensity_guidance}</p>
                                              </div>
                                            )}
                                            {phase.workout_details.volume_notes && (
                                              <div className="p-3 bg-blue-50 rounded-lg">
                                                <p className="text-xs font-semibold text-blue-700 uppercase mb-1">Volume</p>
                                                <p className="text-sm text-blue-900">{phase.workout_details.volume_notes}</p>
                                              </div>
                                            )}
                                            {phase.workout_details.progression_notes && (
                                              <div className="p-3 bg-blue-50 rounded-lg">
                                                <p className="text-xs font-semibold text-blue-700 uppercase mb-1">Progression</p>
                                                <p className="text-sm text-blue-900">{phase.workout_details.progression_notes}</p>
                                              </div>
                                            )}
                                            {phase.workout_details.workout_cycle && phase.workout_details.workout_cycle.length > 0 && (
                                              <div>
                                                <p className="text-xs font-semibold text-gray-700 uppercase mb-2">Weekly Training Cycle</p>
                                                <div className="grid grid-cols-7 gap-1">
                                                  {phase.workout_details.workout_cycle.map((item: any, cycleIdx: number) => (
                                                    <div 
                                                      key={cycleIdx} 
                                                      className={`p-2 rounded text-center text-xs ${
                                                        item.type === 'workout' 
                                                          ? 'bg-blue-100 text-blue-900 font-medium' 
                                                          : 'bg-gray-100 text-gray-600'
                                                      }`}
                                                      title={item.type === 'workout' ? `Workout ${item.workout_index + 1}` : 'Rest Day'}
                                                    >
                                                      <div className="font-semibold mb-0.5">D{cycleIdx + 1}</div>
                                                      <div className="text-[10px] leading-tight">
                                                        {item.type === 'workout' ? `W${item.workout_index + 1}` : 'Rest'}
                                                      </div>
                                                    </div>
                                                  ))}
                                                </div>
                                              </div>
                                            )}
                                          </>
                                        )}
                                      </div>

                                      {/* Nutrition Details Column */}
                                      <div className="p-4 bg-white rounded-lg border border-gray-200 space-y-4">
                                        <h6 className="font-semibold text-green-900 flex items-center gap-2 pb-2 border-b">
                                          <Target className="h-4 w-4" />
                                          Nutrition Plan
                                        </h6>
                                        {phase.meal_details && (
                                          <>
                                            <div className="grid grid-cols-2 gap-3">
                                              <div className="p-3 bg-green-50 rounded-lg">
                                                <p className="text-xs font-semibold text-green-700 uppercase mb-1">Daily Calories</p>
                                                <p className="text-lg font-bold text-green-900">{phase.meal_details.daily_calorie_target}</p>
                                                <p className="text-xs text-green-600">kcal/day</p>
                                              </div>
                                              <div className="p-3 bg-green-50 rounded-lg">
                                                <p className="text-xs font-semibold text-green-700 uppercase mb-1">Macro Split</p>
                                                <p className="text-sm font-medium text-green-900">{phase.meal_details.macro_split}</p>
                                              </div>
                                            </div>
                                            {phase.meal_details.phase_nutrition_focus && (
                                              <div className="p-3 bg-green-50 rounded-lg">
                                                <p className="text-xs font-semibold text-green-700 uppercase mb-1">Nutrition Focus</p>
                                                <p className="text-sm text-green-900">{phase.meal_details.phase_nutrition_focus}</p>
                                              </div>
                                            )}
                                            {phase.meal_details.sample_days && phase.meal_details.sample_days.length > 0 && (
                                              <div className="text-sm text-gray-600">
                                                <span className="font-medium text-gray-900">{phase.meal_details.sample_days.length}</span> sample meal plan(s) available
                                              </div>
                                            )}
                                            {phase.meal_details.grocery_list && phase.meal_details.grocery_list.length > 0 && (
                                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <ShoppingCart className="h-4 w-4 text-green-600" />
                                                <span><span className="font-medium text-gray-900">{phase.meal_details.grocery_list.length}</span> items on shopping list</span>
                                              </div>
                                            )}
                                            {phase.meal_details.meal_prep_sessions && phase.meal_details.meal_prep_sessions.length > 0 && (
                                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <ChefHat className="h-4 w-4 text-purple-600" />
                                                <span><span className="font-medium text-gray-900">{phase.meal_details.meal_prep_sessions.length}</span> prep session(s) planned</span>
                                              </div>
                                            )}
                                          </>
                                        )}
                                      </div>
                                    </div>
                                  </details>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Legacy Workout Days (old schema) */}
                          {(selectedPlan as any).workout_plan?.workouts && (selectedPlan as any).workout_plan.workouts.length > 0 && (
                            <div>
                              <h5 className="font-medium text-gray-900 mb-3">Workout Schedule</h5>
                              <div className="space-y-3">
                                {(selectedPlan as any).workout_plan.workouts.map((workout: any, idx: number) => (
                                  <details key={idx} className="group">
                                    <summary className="p-3 bg-gray-50 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-100 transition-colors">
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <p className="font-medium text-gray-900 text-sm">{workout.day_name}</p>
                                          <p className="text-xs text-gray-600">
                                            {workout.focus} • {workout.duration_minutes} min • {workout.exercises?.length || 0} exercises
                                          </p>
                                        </div>
                                        <CheckCircle2 className="h-4 w-4 text-gray-400 group-open:rotate-90 transition-transform" />
                                      </div>
                                    </summary>
                                    <div className="mt-2 p-4 bg-white rounded-lg border border-gray-200 space-y-3">
                                      {workout.warmup && (
                                        <div>
                                          <p className="text-xs font-semibold text-gray-700 uppercase mb-1">Warmup</p>
                                          <p className="text-sm text-gray-600">{workout.warmup}</p>
                                        </div>
                                      )}
                                      {workout.exercises && workout.exercises.length > 0 && (
                                        <div>
                                          <p className="text-xs font-semibold text-gray-700 uppercase mb-2">Exercises</p>
                                          <div className="space-y-2">
                                            {workout.exercises.map((ex: any, exIdx: number) => (
                                              <div key={exIdx} className="flex justify-between items-start p-2 bg-gray-50 rounded">
                                                <div className="flex-1">
                                                  <p className="text-sm font-medium text-gray-900">{ex.name}</p>
                                                  {ex.notes && <p className="text-xs text-gray-500 mt-1">{ex.notes}</p>}
                                                </div>
                                                <div className="text-right ml-4">
                                                  <p className="text-xs text-gray-600">{ex.sets} × {ex.reps}</p>
                                                  <p className="text-xs text-gray-500">{ex.rest_seconds}s rest</p>
                                                </div>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      )}
                                      {workout.cooldown && (
                                        <div>
                                          <p className="text-xs font-semibold text-gray-700 uppercase mb-1">Cooldown</p>
                                          <p className="text-sm text-gray-600">{workout.cooldown}</p>
                                        </div>
                                      )}
                                    </div>
                                  </details>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}



                    {/* Key Principles & Success Metrics */}
                    {(selectedPlan.key_principles || selectedPlan.success_metrics) && (
                      <div className="border-t pt-6">
                        <div className="grid md:grid-cols-2 gap-6">
                          {selectedPlan.key_principles && selectedPlan.key_principles.length > 0 && (
                            <div>
                              <h5 className="font-medium text-gray-900 mb-3">Key Principles for Success</h5>
                              <ul className="space-y-2">
                                {selectedPlan.key_principles.map((principle: string, idx: number) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                    <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0 mt-0.5" />
                                    <span>{principle}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {selectedPlan.success_metrics && selectedPlan.success_metrics.length > 0 && (
                            <div>
                              <h5 className="font-medium text-gray-900 mb-3">Success Metrics</h5>
                              <ul className="space-y-2">
                                {selectedPlan.success_metrics.map((metric: string, idx: number) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                    <Target className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                                    <span>{metric}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Important Notes */}
                    {selectedPlan.important_notes && (
                      <div className="border-t pt-6">
                        <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                          <div className="flex gap-2">
                            <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                            <div>
                              <h5 className="font-medium text-yellow-900 mb-1">Important Notes</h5>
                              <p className="text-sm text-yellow-800">
                                {selectedPlan.important_notes}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Plan Metadata */}
                    <div className="border-t pt-6 text-xs text-gray-500">
                      <div className="flex justify-between">
                        <span>Created: {formatDate(selectedPlan.created_at)}</span>
                        <span>Last updated: {formatDate(selectedPlan.updated_at)}</span>
                      </div>
                      {scheduleData && (
                        <div className="mt-2">
                          Schedule last recalculated: {formatDate(scheduleData.last_recalculated_at)}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Phase Timeline */}
                {phases.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Phase Timeline</CardTitle>
                      <CardDescription>
                        Track your progress through each phase of your fitness journey
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <PhaseTimeline
                        phases={phases}
                        currentPhaseNumber={phaseStatus?.current_phase?.phase_number || 1}
                      />
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Activate Plan Confirmation Dialog */}
      <AlertDialog open={showActivateDialog} onOpenChange={setShowActivateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Activate this plan?</AlertDialogTitle>
            <AlertDialogDescription>
              You already have an active fitness plan. Activating this plan will pause your
              current active plan. You can switch between plans at any time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => planToActivate && activatePlan(planToActivate.id)}>
              Activate Plan
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Milestone Celebration Dialog */}
      <MilestoneCelebration
        milestone={currentMilestone}
        open={showMilestone}
        onClose={() => setShowMilestone(false)}
      />
    </div>
  );
}


