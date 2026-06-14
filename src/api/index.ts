const BASE_URL = '/api'

function getToken(): string | null {
  return localStorage.getItem('token')
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers,
  })
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('未授权，请重新登录')
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

function get<T>(url: string, params?: Record<string, string | number | boolean>): Promise<T> {
  let queryString = ''
  if (params) {
    const filtered = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
    if (filtered.length > 0) {
      queryString = '?' + filtered.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
    }
  }
  return request<T>(url + queryString)
}

function post<T>(url: string, body?: any): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

function put<T>(url: string, body?: any): Promise<T> {
  return request<T>(url, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  })
}

function del<T = void>(url: string): Promise<T> {
  return request<T>(url, { method: 'DELETE' })
}

export const authApi = {
  login: (data: { username: string; password: string }) => post<{ access_token: string; token_type: string }>('/auth/login', data),
  getMe: () => get<{ id: number; username: string; role: string }>('/auth/me'),
}

export const floorApi = {
  list: () => get<any[]>('/floors'),
  create: (data: { name: string; sort_order?: number }) => post('/floors', data),
  update: (id: number, data: { name: string; sort_order?: number }) => put(`/floors/${id}`, data),
  delete: (id: number) => del(`/floors/${id}`),
}

export const roomApi = {
  list: (params?: { floor_id?: number }) => get<any[]>('/rooms', params),
  create: (data: { room_number: string; floor_id: number; room_type: string; occupancy_status: string; max_visitors: number }) => post('/rooms', data),
  update: (id: number, data: Partial<{ room_number: string; floor_id: number; room_type: string; occupancy_status: string; max_visitors: number }>) => put(`/rooms/${id}`, data),
  delete: (id: number) => del(`/rooms/${id}`),
}

export const residentApi = {
  list: (params?: { search?: string }) => get<any[]>('/residents', params),
  create: (data: { name: string; phone?: string; room_id: number; check_in_date: string; expected_check_out_date?: string }) => post('/residents', data),
  update: (id: number, data: Partial<{ name: string; phone: string; room_id: number; check_in_date: string; expected_check_out_date: string }>) => put(`/residents/${id}`, data),
  delete: (id: number) => del(`/residents/${id}`),
}

export const appointmentApi = {
  list: (params?: { status?: string; search?: string; resident_id?: number }) => get<any[]>('/appointments', params),
  create: (data: { resident_id: number; visitor_name: string; visitor_phone?: string; visitor_id_card?: string; visitor_relation: string; scheduled_start: string; scheduled_end: string; whitelist_id?: number }) => post('/appointments', data),
  update: (id: number, data: Partial<{ visitor_name: string; visitor_phone: string; visitor_id_card: string; visitor_relation: string; scheduled_start: string; scheduled_end: string; status: string }>) => put(`/appointments/${id}`, data),
  delete: (id: number) => del(`/appointments/${id}`),
  search: (params: { appointment_no?: string; visitor_name?: string }) => get<any[]>('/appointments/search', params),
}

export const visitApi = {
  checkin: (data: { appointment_id: number; visitor_id_card?: string; room_id?: number; reject_reason?: string; visit_code_id?: number }) => post('/visits/checkin', data),
  checkinByCode: (data: { code: string; reject_reason?: string }) => post('/visits/checkin/code', data),
  getByCode: (code: string) => get<any>(`/visits/code/${code}`),
  checkout: (data: { visit_id?: number; appointment_id?: number }) => post('/visits/checkout', data),
  listActive: () => get<any[]>('/visits/active'),
}

export const blacklistApi = {
  list: () => get<any[]>('/blacklist'),
  create: (data: { visitor_name: string; visitor_id_card: string; reason: string }) => post('/blacklist', data),
  remove: (id: number) => del(`/blacklist/${id}`),
}

export const whitelistApi = {
  list: (params?: { resident_id?: number }) => get<any[]>('/whitelist', params),
  create: (data: { resident_id: number; visitor_name: string; visitor_phone?: string; visitor_id_card?: string; visitor_relation?: string }) => post('/whitelist', data),
  update: (id: number, data: Partial<{ visitor_name: string; visitor_phone: string; visitor_id_card: string; visitor_relation: string }>) => put(`/whitelist/${id}`, data),
  delete: (id: number) => del(`/whitelist/${id}`),
  getByResident: (resident_id: number) => get<any[]>(`/whitelist/resident/${resident_id}`),
}

export const statisticsApi = {
  dashboard: () => get<{ today_visits: number; active_visitors: number; interception_count: number; overcapacity_count: number; whitelist_visit_count: number; whitelist_ratio: number; visit_code_released_count: number; visit_code_rejected_count: number; pending_deposit_count: number; pending_deposit_amount: number; overdue_item_count: number; abnormal_item_count: number; bill_total_count: number; bill_paid_count: number; bill_settle_rate: number; bill_deduct_count: number; bill_avg_deduct: number; bill_total_deduct: number }>('/statistics/dashboard'),
  roomHeat: (params?: { days?: number }) => get<any[]>('/statistics/room-heat', params),
  interception: (params?: { days?: number }) => get<any[]>('/statistics/interception', params),
  overcapacity: (params?: { days?: number }) => get<any[]>('/statistics/overcapacity', params),
  deductReasons: (params?: { days?: number }) => get<Array<{ reason: string; count: number; total_amount: number }>>('/statistics/deduct-reasons', params),
}

export const depositApi = {
  list: (params?: { status?: string; visitor_name?: string; appointment_id?: number }) => get<any[]>('/deposits', params),
  create: (data: { appointment_id: number; visit_id?: number; visitor_name: string; amount: number }) => post<any>('/deposits', data),
  settle: (id: number, data: { action: 'refund' | 'partial_refund' | 'deduct'; refund_amount?: number; deduct_reason?: string }) => post<any>(`/deposits/${id}/settle`, data),
}

export const itemLoanApi = {
  list: (params?: { status?: string; item_type?: string; visitor_name?: string; appointment_id?: number }) => get<any[]>('/items', params),
  create: (data: { appointment_id: number; visit_id?: number; visitor_name: string; item_type: string; item_name: string; item_identifier?: string; due_return_at?: string }) => post<any>('/items', data),
  returnItem: (id: number, data: { action?: 'return' | 'lost' | 'damaged'; abnormal_reason?: string }) => post<any>(`/items/${id}/return`, data),
}

export const depositItemSummaryApi = {
  get: () => get<{
    pending_deposit_count: number;
    pending_deposit_amount: number;
    overdue_item_count: number;
    abnormal_item_count: number;
    today_collected_count: number;
    today_collected_amount: number;
    item_distribution: Array<{ item_type: string; item_name: string; total_count: number; abnormal_count: number }>;
  }>('/deposit-items/summary'),
}

export interface ChargeItem {
  id: number;
  charge_type: string;
  item_name: string;
  description: string;
  amount: number;
  created_at: string;
}

export interface ElectronicSignature {
  signer_name: string;
  signature_data: string;
  signed_at: string;
  sign_device: string;
}

export interface VisitorBill {
  id: number;
  bill_no: string;
  visit_id: number;
  appointment_id: number;
  visitor_name: string;
  room_number: string;
  resident_name: string;
  deposit_amount: number;
  deposit_refund_amount: number;
  item_damage_fee: number;
  item_lost_fee: number;
  overtime_fee: number;
  other_fee: number;
  total_amount: number;
  actual_paid: number;
  payment_status: string;
  signature_status: string;
  generated_at: string;
  paid_at: string;
  remarks: string;
  operator: string;
  check_in_time: string;
  check_out_time: string;
  charge_items: ChargeItem[];
  signature: ElectronicSignature | null;
}

export const billApi = {
  generate: (data: { visit_id: number; operator?: string }) => post<VisitorBill>('/bills/generate', data),
  get: (id: number) => get<VisitorBill>(`/bills/${id}`),
  getByVisit: (visit_id: number) => get<VisitorBill>(`/bills/visit/${visit_id}`),
  list: (params?: { visitor_name?: string; payment_status?: string; signature_status?: string; bill_no?: string; start_date?: string; end_date?: string }) => get<VisitorBill[]>('/bills', params),
  pay: (id: number, data: { actual_paid: number; remarks?: string; operator?: string }) => post<VisitorBill>(`/bills/${id}/pay`, data),
  sign: (id: number, data: { signer_name: string; signature_data: string; sign_device?: string }) => post<VisitorBill>(`/bills/${id}/sign`, data),
  statistics: (params?: { days?: number }) => get<{
    total_bills: number;
    paid_bills: number;
    settlement_rate: number;
    deduct_count: number;
    total_deduct_amount: number;
    avg_deduct_amount: number;
    deduct_reason_distribution: Array<{ reason: string; count: number; total_amount: number }>;
  }>('/bills/statistics', params),
}
