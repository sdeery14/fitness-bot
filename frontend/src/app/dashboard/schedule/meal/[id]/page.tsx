'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMealDetail } from '@/hooks/use-meal-detail';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Utensils, Clock, Flame } from 'lucide-react';

export default function MealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const mealId = params.id as string;
  const { meal, loading, error, fetchMeal } = useMealDetail();

  useEffect(() => {
    if (mealId) {
      fetchMeal(mealId);
    }
  }, [mealId, fetchMeal]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !meal) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8">
            <p className="text-destructive">Error loading meal: {error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const ingredients = meal.meal_details?.ingredients || [];
  const instructions = meal.meal_details?.instructions || [];
  const prepTime = meal.meal_details?.prep_time_minutes || 0;
  const cookTime = meal.meal_details?.cook_time_minutes || 0;
  const servings = meal.meal_details?.servings || 1;

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{meal.name}</h1>
        <p className="text-muted-foreground capitalize">{meal.meal_type}</p>
      </div>

      {/* Nutrition Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5" />
            Nutrition Information
          </CardTitle>
          <CardDescription>Per serving</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-secondary rounded-lg">
              <p className="text-3xl font-bold text-primary">{meal.calories}</p>
              <p className="text-sm text-muted-foreground">Calories</p>
            </div>
            <div className="text-center p-4 bg-secondary rounded-lg">
              <p className="text-3xl font-bold">{meal.protein_grams.toFixed(1)}g</p>
              <p className="text-sm text-muted-foreground">Protein</p>
            </div>
            <div className="text-center p-4 bg-secondary rounded-lg">
              <p className="text-3xl font-bold">{meal.carbs_grams.toFixed(1)}g</p>
              <p className="text-sm text-muted-foreground">Carbs</p>
            </div>
            <div className="text-center p-4 bg-secondary rounded-lg">
              <p className="text-3xl font-bold">{meal.fats_grams.toFixed(1)}g</p>
              <p className="text-sm text-muted-foreground">Fats</p>
            </div>
          </div>
          {meal.fiber_grams > 0 && (
            <div className="mt-4 text-center">
              <p className="text-sm text-muted-foreground">
                <span className="font-semibold">{meal.fiber_grams.toFixed(1)}g</span> Fiber
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Timing Info */}
      {(prepTime > 0 || cookTime > 0 || servings > 1) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {prepTime > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Prep Time</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{prepTime} min</p>
              </CardContent>
            </Card>
          )}
          {cookTime > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cook Time</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{cookTime} min</p>
              </CardContent>
            </Card>
          )}
          {servings > 1 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Servings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{servings}</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Ingredients */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Utensils className="h-5 w-5" />
            Ingredients
          </CardTitle>
          <CardDescription>{ingredients.length} ingredient{ingredients.length !== 1 ? 's' : ''}</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {ingredients.map((ingredient, index) => (
              <li key={index} className="flex items-start justify-between py-2 border-b last:border-0">
                <div className="flex-1">
                  <p className="font-medium">{ingredient.name}</p>
                  {ingredient.calories && (
                    <p className="text-sm text-muted-foreground">
                      {ingredient.calories} cal
                      {ingredient.protein_grams && ` • ${ingredient.protein_grams.toFixed(1)}g protein`}
                      {ingredient.carbs_grams && ` • ${ingredient.carbs_grams.toFixed(1)}g carbs`}
                      {ingredient.fats_grams && ` • ${ingredient.fats_grams.toFixed(1)}g fat`}
                    </p>
                  )}
                </div>
                <Badge variant="outline">
                  {ingredient.quantity} {ingredient.unit}
                </Badge>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Instructions */}
      {instructions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Preparation Instructions</CardTitle>
            <CardDescription>{instructions.length} step{instructions.length !== 1 ? 's' : ''}</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4">
              {instructions.map((instruction, index) => (
                <li key={index} className="flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                    {index + 1}
                  </div>
                  <p className="flex-1 pt-1">{instruction}</p>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Notes */}
      {meal.meal_details?.notes && (
        <Card>
          <CardHeader>
            <CardTitle>Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{meal.meal_details.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
