"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Utensils, Flame, Clock } from "lucide-react";

interface MealItem {
  food: string;
  portion_size: string;
  calories?: number;
  protein?: number;
  carbs?: number;
  fat?: number;
}

interface Meal {
  id: string;
  name: string;
  meal_type: string;
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fat_grams: number;
  preparation_time_minutes?: number;
  meal_details: {
    items: MealItem[];
    instructions?: string;
  };
}

interface MealCardProps {
  meal: Meal;
  phaseNumber?: number;
  weekNumber?: number;
}

export function MealCard({ meal, phaseNumber, weekNumber }: MealCardProps) {
  const getMealTypeIcon = (type: string) => {
    return <Utensils className="h-5 w-5" />;
  };

  const getMealTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case "breakfast":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "lunch":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "dinner":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "snack":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl">{meal.name}</CardTitle>
            <CardDescription className="mt-1">
              {phaseNumber && `Phase ${phaseNumber}`}
              {weekNumber && ` • Week ${weekNumber}`}
            </CardDescription>
          </div>
          <Badge className={getMealTypeColor(meal.meal_type)} variant="outline">
            {meal.meal_type}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Nutrition Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg">
            <Flame className="h-4 w-4 text-orange-600 mb-1" />
            <p className="text-lg font-bold">{meal.calories}</p>
            <p className="text-xs text-gray-600">Calories</p>
          </div>
          <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg">
            <p className="text-lg font-bold">{meal.protein_grams}g</p>
            <p className="text-xs text-gray-600">Protein</p>
          </div>
          <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg">
            <p className="text-lg font-bold">{meal.carbs_grams}g</p>
            <p className="text-xs text-gray-600">Carbs</p>
          </div>
          <div className="flex flex-col items-center p-3 bg-gray-50 rounded-lg">
            <p className="text-lg font-bold">{meal.fat_grams}g</p>
            <p className="text-xs text-gray-600">Fat</p>
          </div>
        </div>

        {/* Preparation Time */}
        {meal.preparation_time_minutes && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>{meal.preparation_time_minutes} min prep time</span>
          </div>
        )}

        {/* Meal Items */}
        {meal.meal_details?.items && meal.meal_details.items.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-700">Ingredients</h4>
            <ul className="space-y-2">
              {meal.meal_details.items.map((item, index) => (
                <li
                  key={index}
                  className="flex items-start justify-between text-sm border-l-2 border-primary pl-3 py-1"
                >
                  <div className="flex-1">
                    <p className="font-medium">{item.food}</p>
                    <p className="text-gray-600">{item.portion_size}</p>
                  </div>
                  {item.calories && (
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {item.calories} cal
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Instructions */}
        {meal.meal_details?.instructions && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-700">Instructions</h4>
            <p className="text-sm text-gray-600 whitespace-pre-line">
              {meal.meal_details.instructions}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
