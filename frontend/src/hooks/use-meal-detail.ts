'use client';

import { useState, useCallback } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

interface MealDetail {
  id: string;
  name: string;
  meal_type: string;
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fats_grams: number;
  fiber_grams: number;
  meal_details: {
    ingredients?: Array<{
      usda_fdc_id?: string;
      name: string;
      quantity: number;
      unit: string;
      calories?: number;
      protein_grams?: number;
      carbs_grams?: number;
      fats_grams?: number;
    }>;
    instructions?: string[];
    prep_time_minutes?: number;
    cook_time_minutes?: number;
    servings?: number;
    notes?: string;
  };
}

export function useMealDetail() {
  const [meal, setMeal] = useState<MealDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMeal = useCallback(async (mealId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/meals/${mealId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch meal details');
      }

      const data = await response.json();
      setMeal(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  return { meal, loading, error, fetchMeal };
}
