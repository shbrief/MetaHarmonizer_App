/* ------------------------------------------------------------------ */
/*  MetaHarmonizer Dashboard — API Client                             */
/*  Centralised HTTP layer — every component calls these functions.   */
/* ------------------------------------------------------------------ */

import { apiFetch, BASE } from './http';
import type {
    AuditEvent,
    HarmonizationResults,
    HarmonizeAccepted,
    Mapping,
    OntologyMapping,
    OntologySearchResult,
    Overview,
    Paginated,
    QualityMetrics,
    Study,
} from './types';

/** Thin wrapper kept for backwards compatibility: routes legacy `${BASE}/x`
 *  paths through the shared auth-aware fetch (bearer token + 401 refresh). */
async function request<T>(url: string, init?: RequestInit): Promise<T> {
    const path = url.startsWith(BASE) ? url.slice(BASE.length) : url;
    return apiFetch<T>(path, init);
}

/* ---------- Studies ---------- */

export async function listStudies(): Promise<Study[]> {
    return request<Study[]>(`${BASE}/studies`);
}

export async function getOverview(): Promise<Overview> {
    return request<Overview>(`${BASE}/overview`);
}

export async function getStudy(id: string): Promise<Study> {
    return request<Study>(`${BASE}/studies/${id}`);
}

export async function deleteStudy(id: string): Promise<void> {
    await request<void>(`${BASE}/studies/${id}`, { method: 'DELETE' });
}

export async function completeStudy(id: string): Promise<Study> {
    return request<Study>(`${BASE}/studies/${id}/complete`, { method: 'POST' });
}

/* ---------- Harmonize ---------- */

export async function uploadAndHarmonize(file: File): Promise<HarmonizeAccepted> {
    const form = new FormData();
    form.append('file', file);
    return request<HarmonizeAccepted>(`${BASE}/harmonize`, {
        method: 'POST',
        body: form,
    });
}

export async function getHarmonizationResults(
    jobId: string,
): Promise<HarmonizationResults> {
    return request<HarmonizationResults>(`${BASE}/harmonize/${jobId}`);
}

/* ---------- Mappings ---------- */

export async function getStudyMappings(studyId: string): Promise<Mapping[]> {
    return request<Mapping[]>(`${BASE}/mappings/${studyId}`);
}

export async function acceptMapping(mappingId: number): Promise<Mapping> {
    return request<Mapping>(`${BASE}/mappings/${mappingId}/accept`, {
        method: 'POST',
    });
}

export async function rejectMapping(mappingId: number): Promise<Mapping> {
    return request<Mapping>(`${BASE}/mappings/${mappingId}/reject`, {
        method: 'POST',
    });
}

export async function editMapping(
    mappingId: number,
    newField: string,
    note = '',
): Promise<Mapping> {
    return request<Mapping>(`${BASE}/mappings/${mappingId}/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_field: newField, note }),
    });
}

export async function batchUpdateMappings(
    mappingIds: number[],
    action: 'accepted' | 'rejected',
): Promise<{ updated: number; action: string }> {
    return request(`${BASE}/mappings/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mapping_ids: mappingIds, action }),
    });
}

/* ---------- Quality ---------- */

export async function getQualityMetrics(studyId: string): Promise<QualityMetrics> {
    return request<QualityMetrics>(`${BASE}/quality/${studyId}`);
}

/* ---------- Ontology ---------- */

export async function searchOntology(
    query: string,
    ontology = '',
): Promise<OntologySearchResult[]> {
    const params = new URLSearchParams({ query });
    if (ontology) params.set('ontology', ontology);
    return request<OntologySearchResult[]>(`${BASE}/ontology/search?${params}`);
}

export async function getOntologyMappings(
    studyId: string,
): Promise<OntologyMapping[]> {
    return request<OntologyMapping[]>(`${BASE}/ontology/mappings/${studyId}`);
}

/** Batch-suggest ontology terms for a study's unmatched values in one request.
 * Returns a map of mapping id → best candidate term/id/score. */
export async function suggestOntologyTerms(
    studyId: string,
): Promise<Record<string, { term: string; ontology_id: string; score: number }>> {
    const res = await request<{
        suggestions: Record<string, { term: string; ontology_id: string; score: number }>;
    }>(`${BASE}/ontology/suggest/${studyId}`, { method: 'POST' });
    return res.suggestions ?? {};
}

export async function acceptOntologyMapping(id: number): Promise<OntologyMapping> {
    return request<OntologyMapping>(`${BASE}/ontology/mappings/${id}/accept`, { method: 'POST' });
}

export async function rejectOntologyMapping(id: number): Promise<OntologyMapping> {
    return request<OntologyMapping>(`${BASE}/ontology/mappings/${id}/reject`, { method: 'POST' });
}

export async function editOntologyMapping(
    id: number,
    newTerm: string,
    newId = '',
): Promise<OntologyMapping> {
    return request<OntologyMapping>(`${BASE}/ontology/mappings/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_term: newTerm, new_id: newId || undefined }),
    });
}

/* ---------- Export ---------- */

export function getExportUrl(studyId: string, format: 'harmonized' | 'cbioportal' | 'report'): string {
    return `${BASE}/export/${studyId}/${format}`;
}

/* ---------- Audit (admin) ---------- */

export async function queryAudit(params: {
    action?: string;
    study_id?: string;
    actor_id?: number;
    since?: string;
    until?: string;
    cursor?: string;
    limit?: number;
}): Promise<Paginated<AuditEvent>> {
    const qs = new URLSearchParams();
    if (params.action) qs.set('action', params.action);
    if (params.study_id) qs.set('study_id', params.study_id);
    if (params.actor_id != null) qs.set('actor_id', String(params.actor_id));
    if (params.since) qs.set('since', params.since);
    if (params.until) qs.set('until', params.until);
    if (params.cursor) qs.set('cursor', params.cursor);
    if (params.limit) qs.set('limit', String(params.limit));
    const q = qs.toString();
    return request<Paginated<AuditEvent>>(`${BASE}/audit${q ? `?${q}` : ''}`);
}
