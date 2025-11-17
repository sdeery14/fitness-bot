"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Award,
  Flame,
  Dumbbell,
  TrendingDown,
  Trophy,
  Star,
  PartyPopper,
  Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Milestone {
  type: string;
  value: number;
  description: string;
  title: string;
  message: string;
}

interface MilestoneCelebrationProps {
  milestone: Milestone | null;
  open: boolean;
  onClose: () => void;
  onShare?: () => void;
}

const getMilestoneIcon = (type: string) => {
  switch (type) {
    case "streak":
      return Flame;
    case "total_workouts":
      return Dumbbell;
    case "weight_loss":
      return TrendingDown;
    case "adherence_consistency":
      return Trophy;
    default:
      return Star;
  }
};

const getMilestoneColor = (type: string) => {
  switch (type) {
    case "streak":
      return "text-orange-600 bg-orange-100";
    case "total_workouts":
      return "text-blue-600 bg-blue-100";
    case "weight_loss":
      return "text-green-600 bg-green-100";
    case "adherence_consistency":
      return "text-yellow-600 bg-yellow-100";
    default:
      return "text-purple-600 bg-purple-100";
  }
};

const getConfetti = () => {
  const confettiColors = [
    "bg-red-500",
    "bg-blue-500",
    "bg-green-500",
    "bg-yellow-500",
    "bg-purple-500",
    "bg-pink-500",
  ];

  return Array.from({ length: 30 }).map((_, i) => ({
    id: i,
    color: confettiColors[i % confettiColors.length],
    left: `${Math.random() * 100}%`,
    delay: `${Math.random() * 0.5}s`,
    duration: `${2 + Math.random() * 2}s`,
  }));
};

export function MilestoneCelebration({
  milestone,
  open,
  onClose,
  onShare,
}: MilestoneCelebrationProps) {
  const [showConfetti, setShowConfetti] = useState(false);
  const [confettiPieces, setConfettiPieces] = useState<any[]>([]);

  useEffect(() => {
    if (open && milestone) {
      setShowConfetti(true);
      setConfettiPieces(getConfetti());

      // Hide confetti after animation
      const timer = setTimeout(() => {
        setShowConfetti(false);
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [open, milestone]);

  if (!milestone) return null;

  const Icon = getMilestoneIcon(milestone.type);
  const colorClass = getMilestoneColor(milestone.type);

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md relative overflow-hidden">
        {/* Confetti animation */}
        {showConfetti && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {confettiPieces.map((piece) => (
              <div
                key={piece.id}
                className={cn(
                  "absolute w-2 h-2 rounded-full animate-fall",
                  piece.color
                )}
                style={{
                  left: piece.left,
                  top: "-10px",
                  animationDelay: piece.delay,
                  animationDuration: piece.duration,
                }}
              />
            ))}
          </div>
        )}

        {/* Header with icon */}
        <DialogHeader>
          <div className="flex flex-col items-center gap-4 mb-2">
            <div
              className={cn(
                "rounded-full p-4 animate-bounce",
                colorClass
              )}
            >
              <Icon className="h-12 w-12" />
            </div>
            <div className="flex items-center gap-2">
              <PartyPopper className="h-5 w-5 text-yellow-500" />
              <DialogTitle className="text-2xl font-bold text-center">
                {milestone.title}
              </DialogTitle>
              <PartyPopper className="h-5 w-5 text-yellow-500" />
            </div>
          </div>
          <DialogDescription className="text-center text-base">
            {milestone.message}
          </DialogDescription>
        </DialogHeader>

        {/* Milestone details */}
        <div className="flex flex-col items-center gap-4 my-6">
          <Badge
            variant="outline"
            className={cn(
              "text-lg font-bold py-2 px-4 border-2",
              colorClass
            )}
          >
            <Award className="h-5 w-5 mr-2" />
            {milestone.description}
          </Badge>

          {/* Motivational text */}
          <div className="bg-gray-50 rounded-lg p-4 text-center border border-gray-200">
            <p className="text-sm text-gray-700 leading-relaxed">
              {milestone.type === "streak" && "Consistency is the key to success. Keep showing up every day!"}
              {milestone.type === "total_workouts" && "Every rep counts. You're building something great!"}
              {milestone.type === "weight_loss" && "Your dedication is paying off. Stay on track!"}
              {milestone.type === "adherence_consistency" && "High adherence shows commitment. You're crushing it!"}
              {!["streak", "total_workouts", "weight_loss", "adherence_consistency"].includes(milestone.type) && 
                "Amazing progress! Keep up the excellent work!"}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {onShare && (
            <Button
              variant="outline"
              onClick={onShare}
              className="flex-1 gap-2"
            >
              <Share2 className="h-4 w-4" />
              Share
            </Button>
          )}
          <Button onClick={onClose} className="flex-1">
            Continue
          </Button>
        </div>
      </DialogContent>

      <style jsx>{`
        @keyframes fall {
          0% {
            transform: translateY(0) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }
        .animate-fall {
          animation: fall linear forwards;
        }
      `}</style>
    </Dialog>
  );
}
