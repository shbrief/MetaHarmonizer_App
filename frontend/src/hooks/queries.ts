import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteStudy, getOverview, listStudies } from '../api/client';
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

/** Permanently delete a study; refreshes the studies list + overview. */
export function useDeleteStudy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteStudy(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['studies'] });
      qc.invalidateQueries({ queryKey: ['overview'] });
    },
  });
}
