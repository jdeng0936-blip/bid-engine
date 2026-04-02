"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Loader2,
  Save,
  Plus,
  Trash2,
  Trophy,
  XCircle,
  AlertTriangle,
  Users,
  MessageSquare,
  BookOpen,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import api from "@/lib/api";

interface Competitor {
  id?: number;
  competitor_name: string;
  competitor_price?: number | null;
  competitor_result?: string | null;
  competitor_strengths?: string | null;
  notes?: string | null;
}

interface ReviewData {
  id: number;
  project_id: number;
  result: string;
  result_reason?: string;
  our_bid_price?: number | null;
  winning_price?: number | null;
  official_feedback?: string;
  personal_summary?: string;
  lessons_learned?: string;
  improvement_actions?: string;
  competitors: Competitor[];
}

const RESULT_OPTIONS = [
  { value: "won", label: "中标", color: "bg-green-100 text-green-700", icon: Trophy },
  { value: "lost", label: "未中标", color: "bg-red-100 text-red-700", icon: XCircle },
  { value: "disqualified", label: "废标", color: "bg-amber-100 text-amber-700", icon: AlertTriangle },
  { value: "abandoned", label: "放弃投标", color: "bg-slate-100 text-slate-600", icon: XCircle },
];

const COMPETITOR_RESULT_OPTIONS = [
  { value: "won", label: "中标" },
  { value: "lost", label: "未中标" },
  { value: "disqualified", label: "废标" },
];

interface ReviewPanelProps {
  projectId: string;
  projectName?: string;
  budgetAmount?: number;
}

export default function ReviewPanel({ projectId, projectName, budgetAmount }: ReviewPanelProps) {
  const [review, setReview] = useState<ReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 表单
  const [result, setResult] = useState("lost");
  const [resultReason, setResultReason] = useState("");
  const [ourBidPrice, setOurBidPrice] = useState<string>("");
  const [winningPrice, setWinningPrice] = useState<string>("");
  const [officialFeedback, setOfficialFeedback] = useState("");
  const [personalSummary, setPersonalSummary] = useState("");
  const [lessonsLearned, setLessonsLearned] = useState("");
  const [improvementActions, setImprovementActions] = useState("");
  const [competitors, setCompetitors] = useState<Competitor[]>([]);

  // AI 分析
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);

  const fetchReview = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/bid-projects/${projectId}/review`);
      const data = res.data?.data as ReviewData | null;
      if (data) {
        setReview(data);
        setResult(data.result);
        setResultReason(data.result_reason || "");
        setOurBidPrice(data.our_bid_price != null ? String(data.our_bid_price) : "");
        setWinningPrice(data.winning_price != null ? String(data.winning_price) : "");
        setOfficialFeedback(data.official_feedback || "");
        setPersonalSummary(data.personal_summary || "");
        setLessonsLearned(data.lessons_learned || "");
        setImprovementActions(data.improvement_actions || "");
        setCompetitors(data.competitors || []);
      }
    } catch {
      // 404 = 没有复盘记录
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchReview();
  }, [fetchReview]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const body = {
        result,
        result_reason: resultReason || null,
        our_bid_price: ourBidPrice ? parseFloat(ourBidPrice) : null,
        winning_price: winningPrice ? parseFloat(winningPrice) : null,
        official_feedback: officialFeedback || null,
        personal_summary: personalSummary || null,
        lessons_learned: lessonsLearned || null,
        improvement_actions: improvementActions || null,
        competitors: competitors.map(({ competitor_name, competitor_price, competitor_result, competitor_strengths, notes }) => ({
          competitor_name,
          competitor_price,
          competitor_result,
          competitor_strengths,
          notes,
        })),
      };

      if (review) {
        await api.put(`/bid-projects/${projectId}/review`, body);
      } else {
        await api.post(`/bid-projects/${projectId}/review`, body);
      }
      await fetchReview();
    } catch (err: any) {
      alert(err.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const addCompetitor = () => {
    setCompetitors([...competitors, {
      competitor_name: "",
      competitor_price: null,
      competitor_result: null,
      competitor_strengths: null,
      notes: null,
    }]);
  };

  const updateCompetitor = (index: number, field: string, value: any) => {
    setCompetitors(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const removeCompetitor = (index: number) => {
    setCompetitors(prev => prev.filter((_, i) => i !== index));
  };

  // AI 综合分析
  const handleAiAnalyze = async () => {
    setAiAnalyzing(true);
    setAiAnalysis(null);
    try {
      const competitorInfo = competitors.length > 0
        ? competitors.map((c, i) => `${i + 1}. ${c.competitor_name}：报价${c.competitor_price || "未知"}万，结果${c.competitor_result || "未知"}，优势：${c.competitor_strengths || "未知"}`).join("\n")
        : "暂无竞争对手信息";

      const prompt = `你是投标策略分析专家。请根据以下投标项目复盘信息，进行综合分析并给出改进建议。

## 项目信息
- 项目名称：${projectName || "未知"}
- 预算金额：${budgetAmount ? (budgetAmount / 10000).toFixed(1) + "万" : "未知"}
- 我方报价：${ourBidPrice || "未填写"}万
- 中标价格：${winningPrice || "未填写"}万
- 投标结果：${RESULT_OPTIONS.find(o => o.value === result)?.label || result}
- 结果原因：${resultReason || "未填写"}

## 竞争对手
${competitorInfo}

## 采购方反馈
${officialFeedback || "未填写"}

## 业务人员总结
${personalSummary || "未填写"}

请从以下几个维度分析：
1. **报价策略分析**：报价是否合理，与中标价的差距原因
2. **技术方案分析**：根据反馈信息推断技术方案可能的不足
3. **竞争格局分析**：相对竞争对手的优劣势
4. **关键改进点**：下次类似项目最应该优先改进的3个方面
5. **可复用经验**：本次投标中做得好、可以保持的方面`;

      const res = await api.post("/ai/chat", {
        message: prompt,
        history: [],
        stream: false,
      });
      setAiAnalysis(res.data?.data?.reply || "分析失败");
    } catch (err: any) {
      alert(err.response?.data?.detail || "AI 分析失败");
    } finally {
      setAiAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 投标结果 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              投标结果
            </CardTitle>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              {review ? "更新复盘" : "保存复盘"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 结果选择 */}
          <div>
            <label className="mb-2 block text-xs text-slate-500">投标结果</label>
            <div className="flex flex-wrap gap-2">
              {RESULT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    result === opt.value
                      ? opt.color + " ring-2 ring-offset-1 ring-slate-300"
                      : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                  }`}
                  onClick={() => setResult(opt.value)}
                >
                  <opt.icon className="h-4 w-4" />
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 价格对比 */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs text-slate-500">我方报价（万元）</label>
              <Input
                type="number"
                value={ourBidPrice}
                onChange={(e) => setOurBidPrice(e.target.value)}
                placeholder="如 198"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">中标价格（万元）</label>
              <Input
                type="number"
                value={winningPrice}
                onChange={(e) => setWinningPrice(e.target.value)}
                placeholder="如 185"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">结果原因</label>
              <Input
                value={resultReason}
                onChange={(e) => setResultReason(e.target.value)}
                placeholder="如：报价偏高 / 技术方案不够细化"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 竞争对手 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              竞争对手（{competitors.length} 家）
            </CardTitle>
            <Button size="sm" variant="outline" onClick={addCompetitor}>
              <Plus className="mr-1 h-4 w-4" />
              添加对手
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {competitors.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">
              暂无竞争对手信息，点击「添加对手」录入
            </p>
          ) : (
            <div className="space-y-3">
              {competitors.map((comp, idx) => (
                <div key={idx} className="rounded-lg border border-slate-200 p-3 space-y-2">
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-4">
                    <div>
                      <label className="mb-1 block text-xs text-slate-500">企业名称 *</label>
                      <Input
                        value={comp.competitor_name}
                        onChange={(e) => updateCompetitor(idx, "competitor_name", e.target.value)}
                        placeholder="竞争企业名称"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-500">报价（万元）</label>
                      <Input
                        type="number"
                        value={comp.competitor_price ?? ""}
                        onChange={(e) => updateCompetitor(idx, "competitor_price", e.target.value ? parseFloat(e.target.value) : null)}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-slate-500">结果</label>
                      <select
                        className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm"
                        value={comp.competitor_result || ""}
                        onChange={(e) => updateCompetitor(idx, "competitor_result", e.target.value || null)}
                      >
                        <option value="">未知</option>
                        {COMPETITOR_RESULT_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-end">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 text-slate-400 hover:text-red-500"
                        onClick={() => removeCompetitor(idx)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-slate-500">对手优势分析</label>
                    <Input
                      value={comp.competitor_strengths || ""}
                      onChange={(e) => updateCompetitor(idx, "competitor_strengths", e.target.value)}
                      placeholder="如：自有基地、价格优势明显、本地老牌企业"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 官方反馈 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            采购方反馈
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            rows={4}
            value={officialFeedback}
            onChange={(e) => setOfficialFeedback(e.target.value)}
            placeholder="采购方的评标意见、扣分明细、改进建议等（可从公告或沟通中获取）..."
          />
        </CardContent>
      </Card>

      {/* 个人复盘 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            人员复盘
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-xs text-slate-500">复盘总结</label>
            <Textarea
              rows={3}
              value={personalSummary}
              onChange={(e) => setPersonalSummary(e.target.value)}
              placeholder="本次投标过程中的整体感受和关键节点回顾..."
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-500">经验教训</label>
            <Textarea
              rows={3}
              value={lessonsLearned}
              onChange={(e) => setLessonsLearned(e.target.value)}
              placeholder="哪些做得好可以保持？哪些做得不足需要改进？"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-500">改进措施</label>
            <Textarea
              rows={3}
              value={improvementActions}
              onChange={(e) => setImprovementActions(e.target.value)}
              placeholder="针对本次教训，下次投标具体要改进的行动项..."
            />
          </div>
        </CardContent>
      </Card>

      {/* AI 综合分析 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              AI 投标分析
            </CardTitle>
            <Button
              onClick={handleAiAnalyze}
              disabled={aiAnalyzing}
              variant={aiAnalysis ? "outline" : "default"}
            >
              {aiAnalyzing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              {aiAnalyzing ? "分析中..." : aiAnalysis ? "重新分析" : "AI 分析此次投标"}
            </Button>
          </div>
        </CardHeader>
        {aiAnalysis && (
          <CardContent>
            <div className="rounded-lg bg-blue-50 p-4">
              <div className="prose prose-sm max-w-none text-slate-700 whitespace-pre-wrap">
                {aiAnalysis}
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
