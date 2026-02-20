// src/api/viewer.ts
import { API_BASE_URL } from './index';
import type { GraphJSON } from '../utils/graphLayout.ts';

interface ProcedureLocation {
  name: string;
  startLine: number;
  approxEndLine: number;
}

export interface IREpochData {
  before: string;
  after: string;
  procedures: ProcedureLocation[];
  epochName: string;
}

export interface ProcedureMetadata {
  name: string;
  beforeHash: string;
  afterHash: string;
}

export async function fetchProcedureIndex(
  epoch: string
): Promise<ProcedureMetadata[]> {
  const response = await fetch(`${API_BASE_URL}/ir/${epoch}/procedures`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      errorText || `HTTP error fetching procedure index for epoch ${epoch}`
    );
  }
  return response.json();
}

export async function fetchGraphJson(
  epoch: string,
  type: 'before' | 'after'
): Promise<Record<string, GraphJSON>> {
  const response = await fetch(`${API_BASE_URL}/cfg/${epoch}/${type}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      errorText ||
        `HTTP error fetching ${type} CFG for epoch ${epoch}. Status: ${response.status}`
    );
  }

  return response.json();
}

export async function fetchIrCode(
  epoch: string,
  procedureName: string,
  type: 'before' | 'after'
): Promise<string> {
  const irResponse = await fetch(
    `${API_BASE_URL}/ir/${epoch}/${procedureName}/${type}`
  );

  if (!irResponse.ok) {
    const errorText = await irResponse.text();
    throw new Error(
      errorText || `HTTP error fetching IR code. Status: ${irResponse.status}`
    );
  }

  return irResponse.text();
}
