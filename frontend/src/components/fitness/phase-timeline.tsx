"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, CheckCircle2, Circle, Target } from "lucide-react";
import { cn } from "@/lib/utils";

interface PhaseObjective {
  id?: string;
  description: string;
  completed?: boolean;
}

interface Phase {
  id: string;
  phase_number: number;
  name: string;
  objectives: string[] | PhaseObjective[];
  start_date: string;
  end_date: string;
  phase_details?: {
    intensity?: string;
    focus?: string;
    volume?: string;
  };
}

interface PhaseTimelineProps {
  phases: Phase[];
  currentPhaseNumber?: number;
}

export function PhaseTimeline({ phases, currentPhaseNumber }: PhaseTimelineProps) {
  const sortedPhases = useMemo(() => {
    return [...phases].sort((a, b) => a.phase_number - b.phase_number);
  }, [phases]);

  const getPhaseStatus = (phase: Phase) => {
    if (!currentPhaseNumber) return "upcoming";

    if (phase.phase_number < currentPhaseNumber) return "completed";
    if (phase.phase_number === currentPhaseNumber) return "active";
    return "upcoming";
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-300";
      case "active":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "upcoming":
        return "bg-gray-100 text-gray-600 border-gray-300";
      default:
        return "bg-gray-100 text-gray-600 border-gray-300";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-6 w-6 text-green-600" />;
      case "active":
        return <Target className="h-6 w-6 text-blue-600" />;
      case "upcoming":
        return <Circle className="h-6 w-6 text-gray-400" />;
      default:
        return <Circle className="h-6 w-6 text-gray-400" />;
    }
  };

  if (!phases || phases.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Phase Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            No phases defined for this plan.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Phase Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[29px] top-6 bottom-6 w-0.5 bg-gray-200" />

          {/* Phases */}
          <div className="space-y-8">
            {sortedPhases.map((phase, index) => {
              const status = getPhaseStatus(phase);
              const isLast = index === sortedPhases.length - 1;

              return (
                <div key={phase.id || `phase-${phase.phase_number}-${index}`} className="relative">
                  {/* Timeline node */}
                  <div className="absolute left-0 top-0 z-10">
                    {getStatusIcon(status)}
                  </div>

                  {/* Phase content */}
                  <div className="ml-14 pb-4">
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn("text-xs font-semibold", getStatusColor(status))}
                          >
                            Phase {phase.phase_number}
                          </Badge>
                          {status === "active" && (
                            <Badge variant="default" className="text-xs">
                              Current
                            </Badge>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {phase.name}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {formatDate(phase.start_date)} - {formatDate(phase.end_date)}
                        </p>
                      </div>
                    </div>

                    {/* Phase details */}
                    {phase.phase_details && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {phase.phase_details.intensity && (
                          <Badge variant="secondary" className="text-xs">
                            Intensity: {phase.phase_details.intensity}
                          </Badge>
                        )}
                        {phase.phase_details.focus && (
                          <Badge variant="secondary" className="text-xs">
                            Focus: {phase.phase_details.focus}
                          </Badge>
                        )}
                        {phase.phase_details.volume && (
                          <Badge variant="secondary" className="text-xs">
                            Volume: {phase.phase_details.volume}
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* Objectives */}
                    {phase.objectives && phase.objectives.length > 0 && (
                      <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <p className="text-xs font-semibold uppercase text-gray-600 mb-2">
                          Objectives
                        </p>
                        <ul className="space-y-1.5">
                          {phase.objectives.map((obj, objIndex) => {
                            const objectiveText = typeof obj === "string" ? obj : obj.description;
                            const isCompleted = typeof obj === "object" ? obj.completed : status === "completed";
                            const objectiveKey = typeof obj === "object" && obj.id 
                              ? obj.id 
                              : `${phase.id}-obj-${objIndex}`;

                            return (
                              <li
                                key={objectiveKey}
                                className="flex items-start gap-2 text-sm text-gray-700"
                              >
                                {isCompleted ? (
                                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                ) : (
                                  <Circle className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                                )}
                                <span className={isCompleted ? "line-through text-gray-500" : ""}>
                                  {objectiveText}
                                </span>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}

                    {/* Transition indicator */}
                    {!isLast && status !== "upcoming" && (
                      <div className="mt-4 flex items-center text-xs text-gray-500">
                        {status === "active" ? (
                          <span>Next phase begins after completion</span>
                        ) : (
                          <span>Transitioned ✓</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
