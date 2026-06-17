import { useQuery } from '@tanstack/react-query';
import { listStudies } from '../api/client';
import type { Study } from '../api/types';

/** Shared, cached studies list — used by every review/quality/export page. */
export function useStudies() {
  return useQuery<Study[]>({
    queryKey: ['studies'],
    queryFn: listStudies,
  });
}
