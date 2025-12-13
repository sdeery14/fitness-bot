"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SuggestionTemplate {
  id: string;
  title: string;
  icon: string;
  description: string;
  prompt: string;
}

const SUGGESTION_TEMPLATES: SuggestionTemplate[] = [
  {
    id: "general_health",
    title: "General Health & Fitness",
    icon: "🌟",
    description: "Perfect for someone looking to be healthy and active",
    prompt: `I'm looking to improve my overall health and fitness. I'd say I'm at a beginner to intermediate level.

My goals:
- Maintain a healthy weight and feel energized
- Build sustainable exercise habits
- Eat balanced, nutritious meals

My situation:
- Fitness level: Beginner/Intermediate
- Equipment: I have access to a gym with full equipment
- Workout frequency: 3-4 days per week
- Time per workout: 45-60 minutes
- Dietary restrictions: None, but I prefer balanced meals
- Schedule: I prefer working out Monday, Wednesday, Friday, and optionally Saturday. I like morning workouts (6-8 AM) and always rest on Sundays.
- Grocery shopping: Once per week on Sunday mornings
- Meal prep: Batch prep twice weekly (Sunday and Wednesday evenings) for 2 hours each session
- Cooking skill: Intermediate
- Storage: I have meal prep containers and good fridge space
- Health notes: No injuries or conditions to consider

Please create a balanced fitness plan that helps me build healthy habits!`,
  },
  {
    id: "athlete",
    title: "Athletic Performance",
    icon: "🏆",
    description: "For athletes looking to improve performance",
    prompt: `I'm an intermediate to advanced athlete looking to take my performance to the next level.

My goals:
- Increase strength and power
- Improve athletic performance and conditioning
- Optimize nutrition for muscle gain and recovery

My situation:
- Fitness level: Intermediate/Advanced
- Equipment: Full gym access with Olympic lifting equipment
- Workout frequency: 5-6 days per week
- Time per workout: 60-90 minutes
- Dietary restrictions: None, focusing on high-protein diet
- Schedule: I prefer a rolling 5-day training cycle (Day 1-5, then repeat) with one rest day after each cycle. I prefer afternoon/evening workouts (4-7 PM). I have a competition coming up in 12 weeks.
- Grocery shopping: Twice weekly (Sunday and Wednesday) to keep food fresh for high performance
- Meal prep: Large batch prep every 3 days (Sunday, Wednesday, Saturday) for 2-3 hours to support training volume
- Cooking skill: Intermediate to advanced
- Storage: Large fridge and freezer with extensive meal prep containers
- Health notes: No current injuries, experienced with compound lifts

Please create a comprehensive performance-focused plan!`,
  },
  {
    id: "injury_recovery",
    title: "Injury Recovery & Active Rehab",
    icon: "🩹",
    description: "Gentle recovery for those coming back from injury",
    prompt: `I'm recovering from an injury and want to get back into fitness safely and gradually.

My goals:
- Safely regain strength and mobility
- Rebuild fitness while avoiding re-injury
- Support recovery with proper nutrition

My situation:
- Fitness level: Beginner (due to recovery, was intermediate before)
- Equipment: Home equipment (resistance bands, light dumbbells) plus gym access
- Workout frequency: 3 days per week initially
- Time per workout: 30-45 minutes
- Dietary restrictions: Anti-inflammatory diet preferred
- Schedule: Flexible schedule, prefer Monday/Wednesday/Friday with longer rest periods. Morning workouts (7-9 AM) work best. Need to avoid any workout on physical therapy days (Tuesdays and Thursdays).
- Grocery shopping: Weekly on Saturdays to minimize trips during recovery
- Meal prep: Simple batch prep once per week (Saturday afternoons) for 1-2 hours - need easy, anti-inflammatory meals
- Cooking skill: Intermediate, but prefer simple recipes during recovery
- Storage: Good storage capacity with meal prep containers
- Health notes: Recovering from lower back strain - need to avoid heavy spinal loading, focus on core stability and proper movement patterns

Please create a safe, progressive recovery-focused plan!`,
  },
];

interface SuggestionCardsProps {
  onSelectSuggestion: (suggestionPrompt: string) => void;
  onFillInput?: (suggestionPrompt: string) => void;
}

export function SuggestionCards({ onSelectSuggestion, onFillInput }: SuggestionCardsProps) {
  const handleCardClick = (prompt: string) => {
    // If onFillInput is provided, use it to fill the input box
    // Otherwise, send the message directly (fallback to old behavior)
    if (onFillInput) {
      onFillInput(prompt);
    } else {
      onSelectSuggestion(prompt);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4">
      <div className="max-w-4xl w-full">
        <div className="mb-8 text-center">
          <div className="mb-4 text-6xl">💪</div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Start Your Fitness Journey
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            Click a quick-start option to fill the message box, then customize and send
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {SUGGESTION_TEMPLATES.map((template) => (
            <Card
              key={template.id}
              className={cn(
                "p-6 cursor-pointer transition-all duration-200",
                "hover:shadow-lg hover:scale-105 hover:border-blue-500",
                "border-2 border-gray-200 bg-white"
              )}
              onClick={() => handleCardClick(template.prompt)}
            >
              <div className="text-center">
                <div className="text-4xl mb-3">{template.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {template.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {template.description}
                </p>
              </div>
            </Card>
          ))}
        </div>

        <div className="text-center text-sm text-gray-500">
          <p>Or type your own custom fitness goals below to get started</p>
        </div>
      </div>
    </div>
  );
}
