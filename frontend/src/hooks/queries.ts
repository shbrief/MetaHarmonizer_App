import { useQuery } from '@tanstack/react-query';
import { getOverview, listStudies } from '../api/client';
import type { Overview, Study } from '../api/types';

/** Shared, cached studies list — used by every review/quality/export page. */
export function useStudies() {
  return useQuery<Study[]>({
    queryKey: ['studies'],
    queryFn: listStudies,
  });
}

/** Portfolio-wide overview for the home dashboard. */
export function useOverview() {
  return useQuery<Overview>({
    queryKey: ['overview'],
    queryFn: getOverview,
  });
}
