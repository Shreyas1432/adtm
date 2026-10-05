// Preview data for screens whose read endpoints are not built yet (DQ results,
// mapping, reconciliation, audit log are produced by worker jobs). Screens show
// a "preview data" notice when these are used. Replace with live calls as the
// corresponding endpoints land. Copy here avoids em-dashes by request.
import type { Column } from '../api/types';

export const SAMPLE_CONNECTION_ID = '11111111-1111-1111-1111-111111111111';
export const SAMPLE_TABLE = 'AP_SUPPLIERS';

export const sampleColumns: Column[] = [
  { name: 'VENDOR_ID', type: 'NUMBER', nullable: false, pk: true, encryption: 'none' },
  { name: 'VENDOR_NAME', type: 'VARCHAR2', nullable: false, encryption: 'aead' },
  { name: 'TAX_ID', type: 'VARCHAR2', nullable: true, encryption: 'aead_blind_index' },
  { name: 'EMAIL', type: 'VARCHAR2', nullable: true, encryption: 'aead_blind_index' },
  { name: 'BANK_ACCOUNT', type: 'VARCHAR2', nullable: true, encryption: 'aead_blind_index' },
  { name: 'ADDRESS_LINE1', type: 'VARCHAR2', nullable: true, encryption: 'aead' },
  { name: 'STATUS', type: 'VARCHAR2', nullable: false, encryption: 'none' },
  { name: 'COUNTRY_CODE', type: 'VARCHAR2', nullable: true, encryption: 'none' },
  { name: 'CREATION_DATE', type: 'DATE', nullable: false, encryption: 'none' },
];

export const sampleConnections = [
  {
    id: SAMPLE_CONNECTION_ID,
    name: 'ebs-suppliers-ro',
    kind: 'source_ebs',
    host: 'ebs-prod:1521 / EBSPROD',
    secretRef: 'EBS_SUPPLIERS_RO',
    status: 'connected',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    name: 'fusion-target',
    kind: 'target_fusion',
    host: 'fa-prod.oraclecloud.com',
    secretRef: 'FUSION_LOADER',
    status: 'connected',
  },
];

export const sampleDq = [
  { rule: 'null', column: 'VENDOR_NAME', passed: 1284, failed: 0, sample: '' },
  { rule: 'null', column: 'TAX_ID', passed: 1281, failed: 3, sample: '(null) x3' },
  { rule: 'duplicate', column: 'TAX_ID', passed: 1278, failed: 6, sample: 'IE1234567T x2' },
  { rule: 'datatype: number', column: 'VENDOR_ID', passed: 1284, failed: 0, sample: '' },
  { rule: 'length <= 60', column: 'VENDOR_NAME', passed: 1283, failed: 1, sample: '72 chars' },
  { rule: 'date', column: 'CREATION_DATE', passed: 1284, failed: 0, sample: '' },
  { rule: 'ri (country ref)', column: 'COUNTRY_CODE', passed: 1283, failed: 1, sample: '"ZZ" not in ref' },
];

export const sampleMappings = [
  { source: 'VENDOR_NAME', target: 'SupplierName', kind: 'one_to_one', transform: '', approved: true },
  { source: 'TAX_ID', target: 'TaxId', kind: 'one_to_one', transform: '', approved: true },
  { source: 'COUNTRY', target: 'Country', kind: 'xref', transform: 'xref=country, default=??', approved: true },
  { source: 'STATUS', target: 'SupplierStatus', kind: 'lookup', transform: 'lookup=supplier_status', approved: false },
  { source: 'PAYMENT_TERMS', target: 'PaymentTerms', kind: 'static', transform: 'value="NET30"', approved: false, suggestion: true },
];

export const sampleReconciliation = {
  submitted: 1284,
  accepted: 1281,
  rejected: 3,
  sourceCount: 1284,
  expectedCount: 1281,
  actualCount: 1281,
  loadedCount: 1281,
  failedCount: 3,
  unmatchedCount: 0,
  status: 'reconciled',
  evidencePath: 'recon/suppliers/run-1.json',
};

export const sampleAuditLog = [
  { n: 1042, action: 'extract', object: 'suppliers', actor: 'Dev User', hash: '9f2a1c..e7b4', at: '10:21:04' },
  { n: 1043, action: 'dq', object: 'suppliers', actor: 'system', hash: 'c41d8f..a2f1', at: '10:21:40' },
  { n: 1044, action: 'map', object: 'suppliers', actor: 'Dev User', hash: '7b1903..0d33', at: '10:22:10' },
  { n: 1045, action: 'load', object: 'suppliers', actor: 'system', hash: 'a0e7c2..9c51', at: '10:24:02' },
  { n: 1046, action: 'readback', object: 'suppliers', actor: 'system', hash: '2f88a1..b7aa', at: '10:24:20' },
  { n: 1047, action: 'reconcile', object: 'suppliers', actor: 'system', hash: '5d31f0..ee90', at: '10:24:33' },
  { n: 1048, action: 'approve.mapping', object: 'STATUS', actor: 'Dev User', hash: 'e7c4b8..1b02', at: '10:25:10' },
];
