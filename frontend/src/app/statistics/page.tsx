'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  getCompanies,
  getFinancialData,
  explainRatios,
  getPdfPageUrl,
  getPdfPageHighlightUrl,
  getPdfInfo,
  getIndustryAverages,
} from '@/lib/api';
import type {
  CompanyInfo,
  FinancialData,
  FieldMetadata,
  RatioData,
  ZScoreData,
} from '@/types/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Cell,
} from 'recharts';
import {
  Brain,
  Loader2,
  TrendingUp,
  TrendingDown,
  Building2,
  ChevronLeft,
  ChevronRight,
  FileText,
  ZoomIn,
  ZoomOut,
  Target,
  BarChart3,
  X,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Crosshair,
  AlertTriangle,
  Scale,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

/* ================================================================
   CONSTANTS
   ================================================================ */

interface RatioGroup {
  key: string;
  name: string;
  label: string;
  icon: string;
  gradient: string;
  ratios: string[];
}

const RATIO_GROUPS: RatioGroup[] = [
  {
    key: 'liquidity',
    name: 'Khả năng thanh toán',
    label: 'Liquidity',
    icon: '💧',
    gradient: 'from-blue-500/10 to-cyan-500/10',
    ratios: ['A1', 'A2', 'A3'],
  },
  {
    key: 'capital',
    name: 'Cân đối vốn',
    label: 'Capital Structure',
    icon: '🏛️',
    gradient: 'from-violet-500/10 to-purple-500/10',
    ratios: ['B1', 'B2', 'B3'],
  },
  {
    key: 'efficiency',
    name: 'Hiệu quả hoạt động',
    label: 'Efficiency',
    icon: '⚡',
    gradient: 'from-amber-500/10 to-orange-500/10',
    ratios: ['C1', 'C2', 'C3'],
  },
  {
    key: 'profitability',
    name: 'Khả năng sinh lời',
    label: 'Profitability',
    icon: '📈',
    gradient: 'from-emerald-500/10 to-green-500/10',
    ratios: ['D1', 'D2', 'D3'],
  },
];

const RATIO_NAMES: Record<string, string> = {
  A1: 'Thanh toán hiện hành',
  A2: 'Thanh toán nhanh',
  A3: 'Thanh toán tức thì',
  B1: 'Nợ / Tổng tài sản',
  B2: 'Nợ / VCSH',
  B3: 'Khả năng trả lãi',
  C1: 'Vòng quay hàng tồn kho',
  C2: 'Kỳ thu tiền bình quân',
  C3: 'Hiệu suất TSCĐ',
  D1: 'Tỷ suất LN ròng',
  D2: 'ROA',
  D3: 'ROA / LNST',
};

const RATIO_FULL_NAMES: Record<string, string> = {
  A1: 'Hệ số thanh toán hiện hành',
  A2: 'Hệ số thanh toán nhanh',
  A3: 'Hệ số thanh toán tức thì',
  B1: 'Hệ số nợ trên tổng tài sản',
  B2: 'Hệ số nợ trên vốn chủ sở hữu',
  B3: 'Hệ số khả năng trả lãi vay',
  C1: 'Vòng quay hàng tồn kho',
  C2: 'Kỳ thu tiền bình quân',
  C3: 'Hiệu suất sử dụng tài sản cố định',
  D1: 'Tỷ suất lợi nhuận ròng trên doanh thu',
  D2: 'Tỷ suất sinh lời trên tổng tài sản (ROA)',
  D3: 'ROA trên lợi nhuận sau thuế',
};

const THRESHOLDS: Record<string, { value: number; label: string; higherIsBetter: boolean }> = {
  // Nhóm A – Khả năng thanh toán
  // Quy luật: (A1 < 1) hoặc (A2 < 0.5) → Nguy hiểm
  A1: { value: 1.0,   label: '≥ 1.0',    higherIsBetter: true  }, // Current ratio   – threshold nguy hiểm
  A2: { value: 0.5,   label: '≥ 0.5',    higherIsBetter: true  }, // Quick ratio      – threshold nguy hiểm
  A3: { value: 0.2,   label: '≥ 0.2',    higherIsBetter: true  }, // Cash ratio       – chuẩn chung
  // Nhóm B – Cân đối vốn
  // Quy luật: (B1 > TB ngành) hoặc (0 < B3 < 1.5) → Nguy hiểm
  B1: { value: 0.5,   label: '≤ 0.5',    higherIsBetter: false }, // Debt/Assets      – chuẩn chung
  B2: { value: 1.0,   label: '≤ 1.0',    higherIsBetter: false }, // D/E ratio        – chuẩn chung
  B3: { value: 1.5,   label: '≥ 1.5',    higherIsBetter: true  }, // Interest coverage– threshold nguy hiểm
  // Nhóm C – Hiệu quả hoạt động
  // Quy luật: (C1 < TB ngành) hoặc (C2 > TB ngành) → Kém
  C1: { value: 5.0,   label: '≥ 5.0',    higherIsBetter: true  }, // Inventory turnover – chuẩn chung
  C2: { value: 0.125, label: '≤ 0.125',  higherIsBetter: false }, // AR/Revenue ratio  – chuẩn chung
  C3: { value: 3.0,   label: '≥ 3.0',    higherIsBetter: true  }, // Fixed asset turnover – chuẩn chung
  // Nhóm D – Khả năng sinh lời
  // Quy luật: (D1 <= 0) hoặc (D3 < TB ngành) → Kém
  D1: { value: 0.0,   label: '> 0',      higherIsBetter: true  }, // Net profit margin – threshold: phải > 0
  D2: { value: 0.07,  label: '≥ 7%',     higherIsBetter: true  }, // EBIT-based ROA    – chuẩn chung
  D3: { value: 0.05,  label: '≥ 5%',     higherIsBetter: true  }, // Net income ROA    – chuẩn chung
};

function classifyRisk(key: string, value: number | null): 'good' | 'average' | 'risk' {
  if (value === null || value === undefined) return 'risk';
  const threshold = THRESHOLDS[key];
  if (!threshold) return 'average';
  if (threshold.higherIsBetter) {
    if (value >= threshold.value) return 'good';
    if (value >= threshold.value * 0.7) return 'average';
    return 'risk';
  } else {
    if (value <= threshold.value) return 'good';
    if (value <= threshold.value * 1.3) return 'average';
    return 'risk';
  }
}

function formatValue(v: number | null): string {
  if (v === null || v === undefined) return 'N/A';
  if (Math.abs(v) >= 1000) return v.toLocaleString('en-US', { maximumFractionDigits: 2 });
  return v.toFixed(4);
}

function formatCurrency(v: number | string | null): string {
  if (v === null || v === undefined) return 'N/A';
  const num = typeof v === 'string' ? parseFloat(v) : v;
  if (isNaN(num)) return String(v);
  if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(2) + ' tỷ';
  if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(2) + ' triệu';
  return num.toLocaleString('vi-VN');
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isMissingExtractedValue(meta?: FieldMetadata): boolean {
  if (!meta) return true;
  const value = meta.value;

  if (value === null || value === undefined) return true;
  if (typeof value === 'number') return !Number.isFinite(value);

  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized === 'null' || normalized === 'undefined' || normalized === 'n/a' || normalized === 'nan') {
    return true;
  }

  const numeric = Number(normalized.replace(/,/g, ''));
  return Number.isNaN(numeric);
}

function normalizeFinancialData(data: FinancialData): FinancialData {
  const normalizedRatios = Object.fromEntries(
    Object.entries(data.calculated_ratios || {}).map(([ratioKey, ratio]) => {
      const fields = ratio?.fields || {};
      const missingFields = Object.entries(fields)
        .filter(([, meta]) => isMissingExtractedValue(meta))
        .map(([name]) => name);

      const normalizedResult = isFiniteNumber(ratio?.result) ? ratio.result : null;
      const derivedError =
        missingFields.length > 0 && normalizedResult === null
          ? `Missing extracted value: ${missingFields.join(', ')}`
          : ratio?.error;

      return [
        ratioKey,
        {
          ...ratio,
          result: normalizedResult,
          error: derivedError,
          fields,
        },
      ];
    })
  ) as Record<string, RatioData>;

  return {
    ...data,
    extracted_fields: data.extracted_fields || {},
    calculated_ratios: normalizedRatios,
  };
}

/* ================================================================
   PDF DOCUMENT VIEWER COMPONENT
   ================================================================ */

function PdfViewer({
  source,
  pageNumber,
  highlight,
  onClose,
  pageCount,
  onPageChange,
  fieldName,
  fieldValue,
}: {
  source: string;
  pageNumber: number;
  highlight?: { left: number; top: number; right: number; bottom: number };
  onClose: () => void;
  pageCount: number;
  onPageChange: (p: number) => void;
  fieldName?: string;
  fieldValue?: string;
}) {
  const [zoom, setZoom] = useState(1);
  const [imgLoaded, setImgLoaded] = useState(false);
  const [imgError, setImgError] = useState(false);

  const imgUrl = highlight
    ? getPdfPageHighlightUrl(source, pageNumber, highlight, Math.round(150 * zoom))
    : getPdfPageUrl(source, pageNumber, Math.round(150 * zoom));

  useEffect(() => {
    setImgLoaded(false);
    setImgError(false);
  }, [pageNumber, highlight, zoom]);

  return (
    <div className="flex flex-col h-full rounded-xl overflow-hidden border border-border/50 shadow-lg bg-slate-50 dark:bg-slate-950">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-background border-b shrink-0">
        <FileText className="h-4 w-4 text-blue-500" />
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium truncate block">
            {fieldName && (
              <>
                <span className="text-blue-500 font-mono">{fieldName}</span>
                {fieldValue && (
                  <span className="text-muted-foreground text-xs ml-1.5">= {fieldValue}</span>
                )}
                <span className="text-muted-foreground mx-1.5">·</span>
              </>
            )}
            <span className="text-muted-foreground text-xs">
              Trang {pageNumber + 1} / {pageCount}
            </span>
          </span>
        </div>

        {/* Navigation */}
        <div className="flex items-center gap-0.5 bg-muted rounded-md p-0.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => onPageChange(Math.max(0, pageNumber - 1))}
            disabled={pageNumber <= 0}
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </Button>
          <span className="text-xs w-8 text-center font-mono">{pageNumber + 1}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => onPageChange(Math.min(pageCount - 1, pageNumber + 1))}
            disabled={pageNumber >= pageCount - 1}
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Zoom */}
        <div className="flex items-center gap-0.5 bg-muted rounded-md p-0.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <span className="text-xs w-10 text-center font-mono">{Math.round(zoom * 100)}%</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={() => setZoom((z) => Math.min(3, z + 0.25))}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
        </div>

        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* PDF image area */}
      <div className="flex-1 overflow-auto flex items-start justify-center p-4 bg-muted/30">
        {!imgLoaded && !imgError && (
          <div className="flex items-center justify-center h-60">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        )}
        {imgError && (
          <div className="flex flex-col items-center gap-3 py-12 text-muted-foreground">
            <FileText className="h-12 w-12 opacity-40" />
            <p className="text-sm">Không thể tải trang PDF</p>
          </div>
        )}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imgUrl}
          alt={`PDF page ${pageNumber + 1}`}
          className={`max-w-full shadow-xl rounded-md border transition-opacity duration-300 ${imgLoaded ? 'opacity-100' : 'opacity-0 absolute'
            }`}
          onLoad={() => setImgLoaded(true)}
          onError={() => setImgError(true)}
        />
      </div>

      {/* Highlight info */}
      {highlight && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/5 border-t border-red-500/20 text-xs shrink-0">
          <Crosshair className="h-3. w-3.5 text-red-500" />
          <span className="text-red-600 dark:text-red-400 font-medium">Vùng được đánh dấu</span>
          <span className="font-mono text-muted-foreground">
            [{(highlight.left * 100).toFixed(0)}%, {(highlight.top * 100).toFixed(0)}%] →
            [{(highlight.right * 100).toFixed(0)}%, {(highlight.bottom * 100).toFixed(0)}%]
          </span>
        </div>
      )}
    </div>
  );
}

/* ================================================================
   MAIN STATISTICS PAGE
   ================================================================ */

export default function StatisticsPage() {
  const [companies, setCompanies] = useState<CompanyInfo[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [financialData, setFinancialData] = useState<FinancialData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCharts, setShowCharts] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [pageCount, setPageCount] = useState(0);
  const [industryAverages, setIndustryAverages] = useState<Record<string, number>>({});

  // PDF viewer state
  const [pdfViewField, setPdfViewField] = useState<{
    fieldName: string;
    meta: FieldMetadata;
  } | null>(null);
  const [pdfViewPage, setPdfViewPage] = useState(0);

  useEffect(() => {
    getCompanies()
      .then((res) => {
        if (res.success && res.data) {
          setCompanies(res.data);
          if (res.data.length > 0) setSelectedSource(res.data[0].source);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedSource) return;
    setLoading(true);
    setError(null);
    setPdfViewField(null);

    Promise.all([
      getFinancialData(selectedSource),
      getPdfInfo(selectedSource),
      getIndustryAverages(),
    ])
      .then(([finRes, pdfRes, indRes]) => {
        if (finRes.success && finRes.data) {
          setFinancialData(normalizeFinancialData(finRes.data as FinancialData));
        }
        else setError(finRes.error || 'Failed to load data');
        if (pdfRes.success && pdfRes.page_count) setPageCount(pdfRes.page_count);
        if (indRes.success && indRes.data) setIndustryAverages(indRes.data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedSource]);

  const handleViewEvidence = useCallback(
    (fieldName: string, meta: FieldMetadata) => {
      setPdfViewField({ fieldName, meta });
      if (meta.page != null) setPdfViewPage(meta.page);
    },
    []
  );

  const handleClosePdf = useCallback(() => {
    setPdfViewField(null);
  }, []);

  const ruleStats = useMemo(() => {
    if (!financialData) return null;
    const ratios = financialData.calculated_ratios;

    const a1 = ratios['A1']?.result;
    const a2 = ratios['A2']?.result;
    const thanhKhoan = ((a1 != null && a1 < 1) || (a2 != null && a2 < 0.5)) ? 'Nguy hiểm' : 'An toàn';
    const reasonA = thanhKhoan === 'Nguy hiểm'
      ? `A1 < 1 (${a1?.toFixed(2) ?? 'N/A'}) hoặc A2 < 0.5 (${a2?.toFixed(2) ?? 'N/A'})`
      : `A1 >= 1 (${a1?.toFixed(2) ?? 'N/A'}) và A2 >= 0.5 (${a2?.toFixed(2) ?? 'N/A'})`;

    const b1 = ratios['B1']?.result;
    const b3 = ratios['B3']?.result;
    const tb1 = industryAverages['B1'];
    const canDoiVon = ((b1 != null && tb1 != null && b1 > tb1) || (b3 != null && b3 > 0 && b3 < 1.5)) ? 'Nguy hiểm' : 'An toàn';
    const reasonB = canDoiVon === 'Nguy hiểm'
      ? `B1 > TB (${b1?.toFixed(2) ?? 'N/A'} > ${tb1?.toFixed(2) ?? 'N/A'}) hoặc 0 < B3 < 1.5 (${b3?.toFixed(2) ?? 'N/A'})`
      : `B1 <= TB (${b1?.toFixed(2) ?? 'N/A'} <= ${tb1?.toFixed(2) ?? 'N/A'}) và không rơi vào 0 < B3 < 1.5`;

    const c1 = ratios['C1']?.result;
    const c2 = ratios['C2']?.result;
    const tc1 = industryAverages['C1'];
    const tc2 = industryAverages['C2'];
    const hieuQua = ((c1 != null && tc1 != null && c1 < tc1) || (c2 != null && tc2 != null && c2 > tc2)) ? 'Kém' : 'Tốt';
    const reasonC = hieuQua === 'Kém'
      ? `C1 < TB (${c1?.toFixed(2) ?? 'N/A'} < ${tc1?.toFixed(2) ?? 'N/A'}) hoặc C2 > TB (${c2?.toFixed(2) ?? 'N/A'} > ${tc2?.toFixed(2) ?? 'N/A'})`
      : `C1 >= TB và C2 <= TB`;

    const d1 = ratios['D1']?.result;
    const d3 = ratios['D3']?.result;
    const td3 = industryAverages['D3'];
    const sinhLoi = ((d1 != null && d1 <= 0) || (d3 != null && td3 != null && d3 < td3)) ? 'Kém' : 'Tốt';
    const reasonD = sinhLoi === 'Kém'
      ? `D1 <= 0 (${d1?.toFixed(4) ?? 'N/A'}) hoặc D3 < TB (${d3?.toFixed(4) ?? 'N/A'} < ${td3?.toFixed(4) ?? 'N/A'})`
      : `D1 > 0 (${d1?.toFixed(4) ?? 'N/A'}) và D3 >= TB (${d3?.toFixed(4) ?? 'N/A'} >= ${td3?.toFixed(4) ?? 'N/A'})`;

    let overallRiskText = 'Trung bình';
    let overallReason = '';
    if ((thanhKhoan === 'Nguy hiểm' && canDoiVon === 'Nguy hiểm') || (sinhLoi === 'Kém' && canDoiVon === 'Nguy hiểm') || (thanhKhoan === 'Nguy hiểm' && hieuQua === 'Kém')) {
      overallRiskText = 'Rủi ro';
      overallReason = 'Thỏa điều kiện: (Thanh khoản = Nguy hiểm & Cân đối vốn = Nguy hiểm) OR (Sinh lời = Kém & Cân đối vốn = Nguy hiểm) OR (Thanh khoản = Nguy hiểm & Hiệu quả = Kém)';
    } else if (thanhKhoan === 'An toàn' && canDoiVon === 'An toàn' && sinhLoi === 'Tốt' && hieuQua === 'Tốt') {
      overallRiskText = 'Tốt';
      overallReason = 'Thỏa điều kiện: Thanh khoản = An toàn & Cân đối vốn = An toàn & Sinh lời = Tốt & Hiệu quả = Tốt';
    } else {
      overallRiskText = 'Trung bình';
      overallReason = 'Không thuộc trường hợp Rủi ro hay Tốt (Các trạng thái đan xen).';
    }

    return {
      thanhKhoan, reasonA,
      canDoiVon, reasonB,
      hieuQua, reasonC,
      sinhLoi, reasonD,
      overallRiskText, overallReason
    };
  }, [financialData, industryAverages]);

  const selectedCompany = companies.find((c) => c.source === selectedSource);

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden">
      {/* ── Top bar ── */}
      <div className="flex items-center gap-3 px-4 py-2 border-b bg-background/80 backdrop-blur-sm shrink-0 z-10">
        <Building2 className="h-4 w-4 text-primary" />
        <h1 className="text-base font-bold tracking-tight">Phân tích tài chính</h1>
        <div className="w-px h-5 bg-border" />
        <Select value={selectedSource} onValueChange={setSelectedSource}>
          <SelectTrigger className="w-72 h-8 text-sm">
            <SelectValue placeholder="Select company..." />
          </SelectTrigger>
          <SelectContent>
            {companies.map((c) => (
              <SelectItem key={c.source} value={c.source}>
                {c.company} — {c.period}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedCompany && (
          <div className="hidden lg:flex items-center gap-2 text-xs">
            <Badge variant="outline" className="font-normal">{selectedCompany.company}</Badge>
            <Badge variant="outline" className="font-normal">{selectedCompany.period}</Badge>
            <Badge variant="outline" className="font-normal">{selectedCompany.currency}</Badge>
            {ruleStats && (
              <Badge
                className={
                  ruleStats.overallRiskText === 'Rủi ro' ? 'bg-red-500 hover:bg-red-600 border-none text-white' :
                    ruleStats.overallRiskText === 'Tốt' ? 'bg-emerald-500 hover:bg-emerald-600 border-none text-white' :
                      'bg-amber-500 hover:bg-amber-600 border-none text-white'
                }
              >
                Sức khỏe: {ruleStats.overallRiskText}
              </Badge>
            )}
          </div>
        )}
        <div className="ml-auto flex items-center gap-2">
          {pdfViewField && (
            <Badge className="bg-blue-500/10 text-blue-600 border-blue-500/20 gap-1 text-xs">
              <Target className="h-3 w-3" />
              {pdfViewField.fieldName}
            </Badge>
          )}
          <Button
            variant={showCharts ? 'default' : 'outline'}
            size="sm"
            className="h-7 text-xs gap-1.5"
            onClick={() => { setShowCharts(!showCharts); if (!showCharts) setShowComparison(false); }}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Biểu đồ
          </Button>
          <Button
            variant={showComparison ? 'default' : 'outline'}
            size="sm"
            className="h-7 text-xs gap-1.5"
            onClick={() => { setShowComparison(!showComparison); if (!showComparison) setShowCharts(false); }}
          >
            <Scale className="h-3.5 w-3.5" />
            So sánh
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 text-xs shrink-0">{error}</div>
      )}

      {loading && (
        <div className="flex items-center justify-center flex-1 gap-3">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Đang tải dữ liệu tài chính...</span>
        </div>
      )}

      {financialData && !loading && (
        <>
          {/* ── Main content ── */}
          <div className="flex-1 min-h-0 flex">
            {/* Left: ratio groups */}
            <div
              className={`transition-all duration-300 ease-in-out overflow-y-auto p-3 ${pdfViewField ? 'w-1/2' : 'w-full'
                }`}
            >
              <div className={`grid gap-3 ${pdfViewField
                ? 'grid-cols-1'
                : 'grid-cols-2 grid-rows-2 h-full'
                }`}>
                {RATIO_GROUPS.map((group) => (
                  <RatioGroupCard
                    key={group.key}
                    group={group}
                    ratios={financialData.calculated_ratios}
                    extractedFields={financialData.extracted_fields || {}}
                    source={financialData.source}
                    onViewEvidence={handleViewEvidence}
                    activeField={pdfViewField?.fieldName}
                    pdfView={!!pdfViewField}
                    ruleStats={ruleStats}
                  />
                ))}
              </div>
            </div>

            {/* Right: PDF viewer */}
            {pdfViewField && (
              <div className="w-1/2 border-l p-2 shrink-0">
                <PdfViewer
                  source={financialData.source}
                  pageNumber={pdfViewPage}
                  highlight={pdfViewField.meta.location}
                  onClose={handleClosePdf}
                  pageCount={pageCount}
                  onPageChange={setPdfViewPage}
                  fieldName={pdfViewField.fieldName}
                  fieldValue={formatCurrency(pdfViewField.meta.value)}
                />
              </div>
            )}
          </div>

          {/* ── Charts overlay ── */}
          {showCharts && (
            <div className="absolute inset-0 top-[48px] z-20 bg-background/95 backdrop-blur-sm overflow-y-auto p-6">
              <div className="max-w-6xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    Biểu đồ tài chính
                  </h2>
                  <Button variant="outline" size="sm" onClick={() => setShowCharts(false)}>
                    <X className="h-4 w-4 mr-1" /> Đóng
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <OverviewBarChart ratios={financialData.calculated_ratios} />
                  <NormalizedRadarChart ratios={financialData.calculated_ratios} />
                </div>
                <GroupBarCharts ratios={financialData.calculated_ratios} />
              </div>
            </div>
          )}

          {/* ── Z-Score comparison overlay ── */}
          {showComparison && financialData.z_score && (
            <ZScoreOverlay
              zScore={financialData.z_score}
              extractedFields={financialData.extracted_fields || {}}
              source={financialData.source}
              onClose={() => setShowComparison(false)}
              pageCount={pageCount}
              ruleStats={ruleStats}
              company={selectedCompany}
            />
          )}
        </>
      )}
    </div>
  );
}

/* ================================================================
   RATIO GROUP CARD
   ================================================================ */

function RatioGroupCard({
  group,
  ratios,
  extractedFields,
  source,
  onViewEvidence,
  activeField,
  pdfView,
  ruleStats,
}: {
  group: RatioGroup;
  ratios: Record<string, RatioData>;
  extractedFields: Record<string, FieldMetadata>;
  source: string;
  onViewEvidence: (fieldName: string, meta: FieldMetadata) => void;
  activeField?: string;
  pdfView?: boolean;
  ruleStats?: any;
}) {
  const [explaining, setExplaining] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<string | null>(null);

  const risks = group.ratios.map((key) => classifyRisk(key, ratios[key]?.result ?? null));
  const riskCounts = { good: 0, average: 0, risk: 0 };
  risks.forEach((r) => riskCounts[r]++);
  const overallRisk: 'good' | 'average' | 'risk' =
    riskCounts.risk >= 2 ? 'risk' : riskCounts.good >= 2 ? 'good' : 'average';

  const RiskIcon =
    overallRisk === 'good' ? ShieldCheck : overallRisk === 'average' ? ShieldAlert : ShieldX;

  let groupTagText = null;
  if (ruleStats) {
    if (group.key === 'liquidity') groupTagText = `Thanh khoản: ${ruleStats.thanhKhoan}`;
    else if (group.key === 'capital') groupTagText = `Cân đối vốn: ${ruleStats.canDoiVon}`;
    else if (group.key === 'efficiency') groupTagText = `Hiệu quả: ${ruleStats.hieuQua}`;
    else if (group.key === 'profitability') groupTagText = `Sinh lợi: ${ruleStats.sinhLoi}`;
  }

  const handleExplain = async () => {
    setExplaining(true);
    const groupRatios: Record<string, RatioData> = {};
    const groupThresholds: Record<string, { value: number; label: string }> = {};
    for (const key of group.ratios) {
      if (ratios[key]) groupRatios[key] = ratios[key];
      if (THRESHOLDS[key]) groupThresholds[key] = THRESHOLDS[key];
    }
    try {
      const res = await explainRatios({
        group_name: group.name,
        group_label: group.label,
        ratios: groupRatios,
        thresholds: groupThresholds,
      });
      if (res.success) {
        setExplanation(res.explanation || null);
        setRecommendations(res.recommendations || null);
        setShowExplanation(true);
      }
    } catch {
      setExplanation('Failed to generate explanation.');
      setShowExplanation(true);
    } finally {
      setExplaining(false);
    }
  };

  return (
    <>
      <div
        className={`rounded-xl border bg-gradient-to-br ${group.gradient} flex flex-col overflow-hidden transition-shadow hover:shadow-lg`}
      >
        {/* Header */}
        <div className="flex items-center gap-2 px-3 py-2 border-b bg-background/40 backdrop-blur-sm">
          <span className="text-base leading-none">{group.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold leading-none">{group.name}</h3>
              {groupTagText && (
                <span className={`text-xs px-2 py-0.5 rounded-md font-semibold ${groupTagText.includes('Nguy hiểm') || groupTagText.includes('Kém') ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'
                  }`}>
                  {groupTagText}
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{group.label}</p>
          </div>
          <RiskIcon
            className={`h-4.5 w-4.5 shrink-0 ${overallRisk === 'good'
              ? 'text-emerald-500'
              : overallRisk === 'average'
                ? 'text-amber-500'
                : 'text-red-500'
              }`}
          />
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 shrink-0"
            onClick={handleExplain}
            disabled={explaining}
            title="AI Analysis"
          >
            {explaining ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5 text-violet-500" />
            )}
          </Button>
        </div>

        {/* Ratios */}
        <div className={`px-2 py-1.5 space-y-1.5 ${pdfView ? '' : 'flex-1 overflow-y-auto'}`}>
          {group.ratios.map((key) => {
            const ratio = ratios[key];
            if (!ratio) return null;
            return (
              <RatioRow
                key={key}
                ratioKey={key}
                ratio={ratio}
                extractedFields={extractedFields}
                source={source}
                onViewEvidence={onViewEvidence}
                activeField={activeField}
              />
            );
          })}
        </div>
      </div>

      {/* AI Explanation Dialog */}
      <Dialog open={showExplanation} onOpenChange={setShowExplanation}>
        <DialogContent className="max-w-xl max-h-[70vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-500" />
              Phân tích AI — {group.name}
            </DialogTitle>
            <DialogDescription>{group.label}</DialogDescription>
          </DialogHeader>
          {explanation && (
            <div className="prose prose-sm max-w-none text-foreground/80">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
          {recommendations && (
            <div className="mt-3 pt-3 border-t">
              <h5 className="font-medium text-sm text-primary mb-1">Khuyến nghị</h5>
              <div className="prose prose-sm max-w-none text-foreground/70">
                <ReactMarkdown>{recommendations}</ReactMarkdown>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

/* ================================================================
   SINGLE RATIO ROW
   ================================================================ */

function RatioRow({
  ratioKey,
  ratio,
  extractedFields,
  source,
  onViewEvidence,
  activeField,
}: {
  ratioKey: string;
  ratio: RatioData;
  extractedFields: Record<string, FieldMetadata>;
  source: string;
  onViewEvidence: (fieldName: string, meta: FieldMetadata) => void;
  activeField?: string;
}) {
  const risk = classifyRisk(ratioKey, ratio.result);
  const threshold = THRESHOLDS[ratioKey];

  // Merge fields with extracted_fields metadata
  const mergedFields = useMemo(() => {
    const result: Record<string, FieldMetadata> = {};
    for (const [name, f] of Object.entries(ratio.fields || {})) {
      const ext = extractedFields?.[name];
      result[name] = {
        ...f,
        page: f.page ?? ext?.page,
        location: f.location ?? ext?.location,
        chunk_type: f.chunk_type ?? ext?.chunk_type,
        chunk_id: f.chunk_id ?? ext?.chunk_id,
      };
    }
    return result;
  }, [ratio.fields, extractedFields]);

  const fillPercent = useMemo(() => {
    if (ratio.result == null || !threshold) return 0;
    if (threshold.value === 0) return 100;
    return Math.min(Math.abs(ratio.result / threshold.value) * 100, 200);
  }, [ratio.result, threshold]);

  const missingFields = useMemo(() => {
    return new Set(
      Object.entries(mergedFields)
        .filter(([, meta]) => isMissingExtractedValue(meta))
        .map(([name]) => name)
    );
  }, [mergedFields]);

  const ratioHasMissingDependency = useMemo(
    () => Object.keys(ratio.fields || {}).some((name) => missingFields.has(name)),
    [ratio.fields, missingFields]
  );

  const ratioHasCalculationIssue = ratio.result == null && (Boolean(ratio.error) || ratioHasMissingDependency);

  return (
    <div className="rounded-lg bg-background/60 backdrop-blur-sm border px-2.5 py-2 hover:bg-background/80 transition-colors group">
      {/* Row 1: key badge + name + value */}
      <div className="flex items-center gap-2">
        <span
          className={`text-xs font-bold font-mono w-7 text-center rounded-md py-0.5 ${risk === 'good'
            ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-400'
            : risk === 'average'
              ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400'
              : 'bg-red-500/20 text-red-700 dark:text-red-400'
            }`}
        >
          {ratioKey}
        </span>
        <span className="text-sm font-medium flex-1 truncate" title={RATIO_FULL_NAMES[ratioKey]}>
          {RATIO_NAMES[ratioKey]}
        </span>
        <span
          className={`font-mono text-base font-bold tabular-nums ${risk === 'good'
            ? 'text-emerald-600 dark:text-emerald-400'
            : risk === 'average'
              ? 'text-amber-600 dark:text-amber-400'
              : 'text-red-600 dark:text-red-400'
            }`}
        >
          {formatValue(ratio.result)}
        </span>
        {ratioHasCalculationIssue && (
          <span title={ratio.error || 'Cannot compute ratio because one or more extracted values were not detected'}>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="mt-1 h-1 rounded-full bg-muted/80 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${risk === 'good'
            ? 'bg-gradient-to-r from-emerald-400 to-emerald-500'
            : risk === 'average'
              ? 'bg-gradient-to-r from-amber-400 to-amber-500'
              : 'bg-gradient-to-r from-red-400 to-red-500'
            }`}
          style={{ width: `${Math.min(fillPercent, 100)}%` }}
        />
      </div>

      {/* Row 2: formula with evidence tokens */}
      <div className="mt-1.5 flex items-start gap-1">
        <span className="text-xs text-muted-foreground/60 italic mt-0.5 shrink-0">f(x)</span>
        <FormulaTokens
          formula={ratio.formula}
          fields={mergedFields}
          source={source}
          onViewEvidence={onViewEvidence}
          activeField={activeField}
          missingFields={missingFields}
          showWarnings={ratioHasCalculationIssue}
        />
        <span className="text-xs text-muted-foreground/60 mt-0.5 shrink-0 ml-auto">
          {threshold?.label}
        </span>
      </div>
    </div>
  );
}

/* ================================================================
   FORMULA TOKENS WITH CLICKABLE EVIDENCE BUTTONS
   ================================================================ */

function FormulaTokens({
  formula,
  fields,
  source,
  onViewEvidence,
  activeField,
  missingFields,
  showWarnings,
}: {
  formula: string;
  fields: Record<string, FieldMetadata>;
  source: string;
  onViewEvidence: (fieldName: string, meta: FieldMetadata) => void;
  activeField?: string;
  missingFields?: Set<string>;
  showWarnings?: boolean;
}) {
  const tokens = useMemo(() => {
    if (!formula) return [];
    const fieldNames = Object.keys(fields || {});
    if (fieldNames.length === 0) return [{ text: formula, isField: false as const }];

    const sorted = [...fieldNames].sort((a, b) => b.length - a.length);
    const escaped = sorted.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp(`(${escaped.join('|')})`, 'g');

    const result: { text: string; isField: boolean; fieldName?: string }[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(formula)) !== null) {
      if (match.index > lastIndex) {
        result.push({ text: formula.slice(lastIndex, match.index), isField: false });
      }
      result.push({ text: match[1], isField: true, fieldName: match[1] });
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < formula.length) {
      result.push({ text: formula.slice(lastIndex), isField: false });
    }
    return result;
  }, [formula, fields]);

  return (
    <span className="inline-flex flex-wrap items-center gap-0.5 text-sm leading-relaxed">
      {tokens.map((tok, i) => {
        if (!(tok.isField && tok.fieldName && fields[tok.fieldName])) {
          return <span key={i} className="text-muted-foreground/70">{tok.text}</span>;
        }

        const fieldMeta = fields[tok.fieldName];
        const fieldMissing = missingFields?.has(tok.fieldName) ?? false;
        const hasEvidence = fieldMeta.page != null;

        const title = fieldMissing
          ? `${tok.fieldName}: value was not detected`
          : `${tok.fieldName} = ${formatCurrency(fieldMeta.value ?? 'N/A')} · Page ${(fieldMeta.page ?? 0) + 1}`;

        return (
          <button
            key={i}
            type="button"
            onClick={() => {
              if (!hasEvidence || fieldMissing) return;
              onViewEvidence(tok.fieldName!, fieldMeta);
            }}
            className={`inline-flex items-center gap-0.5 font-mono rounded px-1 py-0 transition-all duration-200 ${fieldMissing
              ? 'text-amber-600 dark:text-amber-400 bg-amber-500/10 cursor-not-allowed'
              : hasEvidence
                ? activeField === tok.fieldName
                  ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 ring-1 ring-blue-500/40 shadow-sm cursor-pointer'
                  : 'text-primary/70 hover:bg-primary/10 hover:text-primary cursor-pointer'
                : 'text-muted-foreground/60 cursor-not-allowed'
              }`}
            title={title}
          >
            {tok.text}
            {showWarnings && fieldMissing ? (
              <AlertTriangle className="h-2.5 w-2.5 text-amber-500" />
            ) : (
              <Target className="h-2.5 w-2.5 opacity-40 group-hover:opacity-70" />
            )}
          </button>
        );
      })}
    </span>
  );
}

/* ================================================================
   CHART COMPONENTS
   ================================================================ */

const CHART_COLORS = ['#3b82f6', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function OverviewBarChart({ ratios }: { ratios: Record<string, RatioData> }) {
  const data = Object.entries(ratios)
    .filter(([, r]) => isFiniteNumber(r.result))
    .map(([key, r]) => ({
      name: key,
      value: r.result,
      risk: classifyRisk(key, r.result),
    }));

  return (
    <Card>
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          All Ratios Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(value) => [Number(value).toFixed(4), 'Value']}
              contentStyle={{ borderRadius: 8, border: '1px solid hsl(var(--border))' }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={entry.risk === 'good' ? '#22c55e' : entry.risk === 'average' ? '#f59e0b' : '#ef4444'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function NormalizedRadarChart({ ratios }: { ratios: Record<string, RatioData> }) {
  const data = Object.entries(ratios)
    .filter(([, r]) => isFiniteNumber(r.result))
    .map(([key, r]) => {
      const threshold = THRESHOLDS[key];
      let normalized: number | null = null;
      if (threshold && r.result !== null) {
        const v = r.result;
        const t = threshold.value;
        if (threshold.higherIsBetter) {
          // Công thức logistic: 2v/(v+t)
          // v=0 → 0, v=t → 1.0, v→∞ → tiệm cận 2 (không bao giờ bằng đúng 2)
          normalized = (2 * v) / (v + t);
        } else {
          // Càng thấp càng tốt, invert: 2t/(v+t)
          // v=0 → 2 (tốt nhất), v=t → 1.0, v→∞ → tiệm cận 0
          normalized = (2 * t) / (v + t);
        }
      } else if (r.result !== null) {
        normalized = r.result;
      }
      return { name: key, value: normalized, fullMark: 2 };
    });

  const legendGroups = [
    { keys: ['A1', 'A2', 'A3'], label: 'càng cao càng tốt', dir: 'up' },
    { keys: ['B1', 'B2'], label: 'càng thấp càng tốt', dir: 'down' },
    { keys: ['B3'], label: 'càng cao càng tốt', dir: 'up' },
    { keys: ['C1', 'C3'], label: 'càng cao càng tốt', dir: 'up' },
    { keys: ['C2'], label: 'càng thấp càng tốt', dir: 'down' },
    { keys: ['D1', 'D2', 'D3'], label: 'càng cao càng tốt', dir: 'up' },
  ];

  return (
    <Card>
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingDown className="h-4 w-4 text-primary" />
          Normalized Radar
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <ResponsiveContainer width="100%" height={260}>
          <RadarChart data={data}>
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis dataKey="name" tick={{ fontSize: 10 }} />
            <PolarRadiusAxis tick={{ fontSize: 9 }} domain={[0, 2]} tickCount={3} />
            <Radar name="Chỉ số" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            <Tooltip formatter={(value) => [Number(value).toFixed(3), 'Normalized']} />
          </RadarChart>
        </ResponsiveContainer>
        {/* Legend giải thích hướng tốt/xấu */}
        <div className="mt-2 pt-2 border-t space-y-1.5">
          <p className="text-[10px] text-muted-foreground">
            Trục radar: <span className="text-foreground font-medium">1.0</span> = đạt ngưỡng &nbsp;·&nbsp;
            <span className="text-foreground font-medium">0–2</span> (tiệm cận, không cắt cứng)
          </p>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1">
            {legendGroups.map(({ keys, label, dir }) => (
              <div key={keys.join()} className="flex items-center gap-1 text-[11px]">
                {dir === 'up' ? (
                  <TrendingUp className="h-3 w-3 text-green-500 shrink-0" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-400 shrink-0" />
                )}
                <span className="font-semibold">{keys.join(', ')}</span>
                <span className="text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function GroupBarCharts({ ratios }: { ratios: Record<string, RatioData> }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {RATIO_GROUPS.map((group, gi) => {
        const data = group.ratios
          .filter((key) => isFiniteNumber(ratios[key]?.result))
          .map((key) => ({
            name: key,
            value: ratios[key]?.result,
            threshold: THRESHOLDS[key]?.value ?? 0,
          }));
        return (
          <Card key={group.key}>
            <CardHeader className="pb-1 px-3 py-2">
              <CardTitle className="text-xs font-medium flex items-center gap-1">
                <span>{group.icon}</span> {group.label}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-2">
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={data} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 9 }} />
                  <Tooltip formatter={(value) => [Number(value).toFixed(4), '']} contentStyle={{ borderRadius: 8 }} />
                  <Bar dataKey="value" name="Value" fill={CHART_COLORS[gi % CHART_COLORS.length]} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="threshold" name="Threshold" fill="#94a3b8" radius={[3, 3, 0, 0]} opacity={0.5} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/* ================================================================
   Z-SCORE COMPARISON OVERLAY
   ================================================================ */

const Z_VARIABLE_NAMES: Record<string, string> = {
  X1: 'Vốn lưu động / Tổng tài sản',
  X2: 'LN sau thuế chưa phân phối / Tổng TS',
  X3: '(EBIT + Chi phí lãi vay) / Tổng TS',
  X4: 'Vốn chủ sở hữu / Tổng nợ phải trả',
  X5: 'Doanh thu thuần / Tổng tài sản',
};

const Z_COEFFICIENTS_MAP: Record<string, number> = {
  X1: 0.717,
  X2: 0.847,
  X3: 3.107,
  X4: 0.420,
  X5: 0.998,
};

function ZScoreOverlay({
  zScore,
  extractedFields,
  source,
  onClose,
  pageCount,
  ruleStats,
  company,
}: {
  zScore: ZScoreData;
  extractedFields: Record<string, FieldMetadata>;
  source: string;
  onClose: () => void;
  pageCount: number;
  ruleStats?: any;
  company?: any;
}) {
  // Local PDF viewer state — lives inside the overlay so it's not hidden
  const [localPdfField, setLocalPdfField] = useState<{
    fieldName: string;
    meta: FieldMetadata;
  } | null>(null);
  const [localPdfPage, setLocalPdfPage] = useState(0);

  const handleViewEvidence = useCallback(
    (fieldName: string, meta: FieldMetadata) => {
      setLocalPdfField({ fieldName, meta });
      if (meta.page != null) setLocalPdfPage(meta.page);
    },
    []
  );

  const classificationConfig = {
    safe: {
      label: 'Doanh nghiệp an toàn – tài chính khoẻ mạnh',
      bg: 'from-emerald-500/10 to-green-500/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-600 dark:text-emerald-400',
      badgeBg: 'bg-emerald-500/15',
      icon: ShieldCheck,
      range: 'Z > 2.99',
    },
    grey: {
      label: 'Vùng xám – không rõ ràng',
      bg: 'from-amber-500/10 to-yellow-500/10',
      border: 'border-amber-500/30',
      text: 'text-amber-600 dark:text-amber-400',
      badgeBg: 'bg-amber-500/15',
      icon: ShieldAlert,
      range: '1.81 < Z ≤ 2.99',
    },
    danger: {
      label: 'Nguy cơ phá sản cao',
      bg: 'from-red-500/10 to-orange-500/10',
      border: 'border-red-500/30',
      text: 'text-red-600 dark:text-red-400',
      badgeBg: 'bg-red-500/15',
      icon: ShieldX,
      range: 'Z ≤ 1.81',
    },
    unknown: {
      label: 'Không thể đánh giá',
      bg: 'from-slate-500/10 to-gray-500/10',
      border: 'border-slate-500/30',
      text: 'text-slate-600 dark:text-slate-400',
      badgeBg: 'bg-slate-500/15',
      icon: AlertTriangle,
      range: 'N/A',
    },
  };

  const config = classificationConfig[zScore.classification] || classificationConfig.unknown;
  const ClassIcon = config.icon;

  // Merge fields with extractedFields for grounding metadata
  const mergedVariableFields = useMemo(() => {
    const result: Record<string, Record<string, FieldMetadata>> = {};
    for (const [xName, xInfo] of Object.entries(zScore.variables)) {
      const merged: Record<string, FieldMetadata> = {};
      for (const [fname, fmeta] of Object.entries(xInfo.fields || {})) {
        const ext = extractedFields?.[fname];
        merged[fname] = {
          ...fmeta,
          page: fmeta.page ?? ext?.page,
          location: fmeta.location ?? ext?.location,
          chunk_type: fmeta.chunk_type ?? ext?.chunk_type,
          chunk_id: fmeta.chunk_id ?? ext?.chunk_id,
        };
      }
      result[xName] = merged;
    }
    return result;
  }, [zScore.variables, extractedFields]);

  return (
    <div className="absolute inset-0 top-[48px] z-20 bg-background/95 backdrop-blur-sm flex">
      {/* Left/Main content */}
      <div className={`transition-all duration-300 ease-in-out overflow-y-auto p-4 ${localPdfField ? 'w-1/2' : 'w-full'}`}>
        <div className={`${localPdfField ? '' : 'max-w-7xl'} mx-auto space-y-4`}>
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Scale className="h-5 w-5 text-primary" />
              So sánh tình trạng tài chính — {company?.company} ({company?.period})
            </h2>
            <div className="flex items-center gap-2">
              {localPdfField && (
                <Badge className="bg-blue-500/10 text-blue-600 border-blue-500/20 gap-1 text-xs">
                  <Target className="h-3 w-3" />
                  {localPdfField.fieldName}
                </Badge>
              )}
              <Button variant="outline" size="sm" onClick={onClose}>
                <X className="h-4 w-4 mr-1" /> Đóng
              </Button>
            </div>
          </div>

          {/* Two Columns */}
          <div className={`grid gap-5 ${localPdfField ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>

            {/* Left Column: Thống kê theo luật */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-primary" />
                Thống kê theo luật
              </h3>

              {/* Sức khỏe tài chính Hero */}
              {ruleStats && (
                <Card className={`border-2 overflow-hidden ${ruleStats.overallRiskText === 'Rủi ro' ? 'bg-red-500/10 border-red-500/30' :
                  ruleStats.overallRiskText === 'Tốt' ? 'bg-emerald-500/10 border-emerald-500/30' :
                    'bg-amber-500/10 border-amber-500/30'
                  }`}>
                  <CardContent className="py-5 px-5">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`p-2.5 rounded-2xl ${ruleStats.overallRiskText === 'Rủi ro' ? 'bg-red-500/20 text-red-600' :
                        ruleStats.overallRiskText === 'Tốt' ? 'bg-emerald-500/20 text-emerald-600' :
                          'bg-amber-500/20 text-amber-600'
                        }`}>
                        {ruleStats.overallRiskText === 'Rủi ro' ? <ShieldX className="h-7 w-7" /> :
                          ruleStats.overallRiskText === 'Tốt' ? <ShieldCheck className="h-7 w-7" /> :
                            <AlertTriangle className="h-7 w-7" />}
                      </div>
                      <div>
                        <p className="text-[13px] text-muted-foreground font-medium mb-0.5">Sức khỏe tài chính tổng thể</p>
                        <p className={`text-2xl font-black ${ruleStats.overallRiskText === 'Rủi ro' ? 'text-red-600 dark:text-red-400' :
                          ruleStats.overallRiskText === 'Tốt' ? 'text-emerald-600 dark:text-emerald-400' :
                            'text-amber-600 dark:text-amber-400'
                          }`}>
                          {ruleStats.overallRiskText}
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-foreground/80 bg-background/50 p-2.5 rounded-lg border">
                      <strong>Lý do:</strong> {ruleStats.overallReason}
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Chi tiết Luật */}
              {ruleStats && (
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <Card className="hover:shadow-md transition-shadow hover:border-primary/50 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 bottom-0 w-1 ${ruleStats.thanhKhoan === 'Nguy hiểm' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                    <CardContent className="p-3">
                      <div className="flex justify-between items-center mb-1.5">
                        <h4 className="font-bold text-[13px] tracking-tight text-foreground/90">A. Khả năng thanh khoản</h4>
                        <Badge variant={ruleStats.thanhKhoan === 'Nguy hiểm' ? 'destructive' : 'default'} className={`uppercase text-[10px] px-1.5 py-0 ${ruleStats.thanhKhoan === 'An toàn' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}`}>{ruleStats.thanhKhoan}</Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground/80 leading-relaxed bg-muted/40 p-1.5 rounded border border-border/50">
                        <span className="font-semibold text-muted-foreground">Lý do:</span> {ruleStats.reasonA}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="hover:shadow-md transition-shadow hover:border-primary/50 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 bottom-0 w-1 ${ruleStats.canDoiVon === 'Nguy hiểm' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                    <CardContent className="p-3">
                      <div className="flex justify-between items-center mb-1.5">
                        <h4 className="font-bold text-[13px] tracking-tight text-foreground/90">B. Cân đối vốn</h4>
                        <Badge variant={ruleStats.canDoiVon === 'Nguy hiểm' ? 'destructive' : 'default'} className={`uppercase text-[10px] px-1.5 py-0 ${ruleStats.canDoiVon === 'An toàn' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}`}>{ruleStats.canDoiVon}</Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground/80 leading-relaxed bg-muted/40 p-1.5 rounded border border-border/50">
                        <span className="font-semibold text-muted-foreground">Lý do:</span> {ruleStats.reasonB}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="hover:shadow-md transition-shadow hover:border-primary/50 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 bottom-0 w-1 ${ruleStats.hieuQua === 'Kém' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                    <CardContent className="p-3">
                      <div className="flex justify-between items-center mb-1.5">
                        <h4 className="font-bold text-[13px] tracking-tight text-foreground/90">C. Hiệu quả hoạt động</h4>
                        <Badge variant={ruleStats.hieuQua === 'Kém' ? 'destructive' : 'default'} className={`uppercase text-[10px] px-1.5 py-0 ${ruleStats.hieuQua === 'Tốt' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}`}>{ruleStats.hieuQua}</Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground/80 leading-relaxed bg-muted/40 p-1.5 rounded border border-border/50">
                        <span className="font-semibold text-muted-foreground">Lý do:</span> {ruleStats.reasonC}
                      </p>
                    </CardContent>
                  </Card>
                  <Card className="hover:shadow-md transition-shadow hover:border-primary/50 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 bottom-0 w-1 ${ruleStats.sinhLoi === 'Kém' ? 'bg-red-500' : 'bg-emerald-500'}`} />
                    <CardContent className="p-3">
                      <div className="flex justify-between items-center mb-1.5">
                        <h4 className="font-bold text-[13px] tracking-tight text-foreground/90">D. Khả năng sinh lợi</h4>
                        <Badge variant={ruleStats.sinhLoi === 'Kém' ? 'destructive' : 'default'} className={`uppercase text-[10px] px-1.5 py-0 ${ruleStats.sinhLoi === 'Tốt' ? 'bg-emerald-500 hover:bg-emerald-600' : ''}`}>{ruleStats.sinhLoi}</Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground/80 leading-relaxed bg-muted/40 p-1.5 rounded border border-border/50">
                        <span className="font-semibold text-muted-foreground">Lý do:</span> {ruleStats.reasonD}
                      </p>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>

            {/* Right Column: Thống kê thông thường Score (Altman Modified) */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Thống kê thông thường Score (Altman Modified)
              </h3>

              {/* Z-Score Hero */}
              <Card className={`bg-gradient-to-br ${config.bg} ${config.border} border-2 overflow-hidden`}>
                <CardContent className="py-4 px-5">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-2xl ${config.badgeBg}`}>
                        <ClassIcon className={`h-6 w-6 ${config.text}`} />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-medium mb-0.5">Z-Score</p>
                        <p className={`text-2xl font-black font-mono tabular-nums ${config.text}`}>
                          {zScore.z_value !== null ? zScore.z_value.toFixed(4) : 'N/A'}
                        </p>
                      </div>
                    </div>
                    <div className="flex-1 text-right">
                      <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg ${config.badgeBg} ${config.text} font-semibold text-sm`}>
                        <ClassIcon className="h-3.5 w-3.5" />
                        {config.label}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1.5">
                        Công thức: <span className="font-mono">{zScore.z_formula}</span>
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* X1–X5 Variable Cards */}
              <div className="flex flex-col gap-1.5">
                {Object.entries(zScore.variables).map(([xName, xInfo]) => {
                  const coeff = Z_COEFFICIENTS_MAP[xName] ?? 0;
                  const xResult = xInfo.result;

                  return (
                    <Card key={xName} className="hover:shadow-sm transition-shadow rounded-md">
                      <CardContent className="p-1.5 flex items-stretch gap-2 bg-background">
                        {/* Details (Name + Formula) */}
                        <div className="flex-1 min-w-0 flex flex-col justify-center gap-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[10px] font-bold font-mono bg-primary/10 text-primary px-1.5 py-0 rounded-sm shrink-0">
                              {xName}
                            </span>
                            <span className="text-[11px] font-semibold text-foreground/90 truncate" title={Z_VARIABLE_NAMES[xName]}>
                              {Z_VARIABLE_NAMES[xName]}
                            </span>
                          </div>
                          
                          <div className="flex items-start gap-1 bg-muted/40 px-1.5 py-1 rounded-sm border border-border/40">
                            <span className="text-[10px] text-muted-foreground/60 italic shrink-0 leading-tight">f(x)=</span>
                            <div className="text-[10px] leading-tight flex-1">
                              <FormulaTokens
                                formula={xInfo.formula}
                                fields={mergedVariableFields[xName] || {}}
                                source={source}
                                onViewEvidence={handleViewEvidence}
                                activeField={localPdfField?.fieldName}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Calculation Block */}
                        <div className="flex flex-col items-end justify-center shrink-0 pl-2 border-l border-border/50 min-w-[90px]">
                          <Badge variant="secondary" className="text-[9px] font-mono px-1 py-0 bg-muted/80 mb-1 rounded-sm">
                            ×{coeff}
                          </Badge>
                          <div className="flex flex-col items-end">
                            <span className="text-[11px] font-medium font-mono tabular-nums text-foreground/80 leading-none">
                              {xResult !== null ? xResult.toFixed(4) : 'N/A'}
                            </span>
                            {xResult !== null && (
                              <div className="flex items-center gap-0.5 mt-0.5">
                                <span className="text-[9px] text-muted-foreground">→</span>
                                <span className="text-[12px] font-bold font-mono tabular-nums text-primary leading-none">
                                  {(coeff * xResult).toFixed(4)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Right: PDF viewer (inside the overlay) */}
      {localPdfField && (
        <div className="w-1/2 border-l p-2 shrink-0">
          <PdfViewer
            source={source}
            pageNumber={localPdfPage}
            highlight={localPdfField.meta.location}
            onClose={() => setLocalPdfField(null)}
            pageCount={pageCount}
            onPageChange={setLocalPdfPage}
            fieldName={localPdfField.fieldName}
            fieldValue={formatCurrency(localPdfField.meta.value)}
          />
        </div>
      )}
    </div>
  );
}
