/**
 * ChapterFeedback 组件测试
 *
 * 测试覆盖：
 * 1. 默认渲染三个操作按钮（采纳/修改/拒绝）
 * 2. 点击"修改"进入编辑模式
 * 3. 点击"采纳"调用 API 并显示已采纳状态
 * 4. 编辑模式取消回到默认状态
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ChapterFeedback from "@/components/business/chapter-feedback";

// Mock api 模块
vi.mock("@/lib/api", () => ({
  default: {
    post: vi.fn().mockResolvedValue({ data: { data: { status: "recorded" } } }),
  },
}));

const defaultProps = {
  projectId: 92,
  chapterNo: "1",
  chapterTitle: "工程概况",
  content: "华阳一矿1301运输巷位于...",
};

describe("ChapterFeedback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("渲染三个操作按钮", () => {
    render(<ChapterFeedback {...defaultProps} />);

    expect(screen.getByText("采纳")).toBeInTheDocument();
    expect(screen.getByText("修改")).toBeInTheDocument();
    expect(screen.getByText("拒绝")).toBeInTheDocument();
  });

  it("点击修改进入编辑模式", async () => {
    const user = userEvent.setup();
    render(<ChapterFeedback {...defaultProps} />);

    await user.click(screen.getByText("修改"));

    expect(screen.getByPlaceholderText("修改后的内容...")).toBeInTheDocument();
    expect(screen.getByText("提交修改")).toBeInTheDocument();
    expect(screen.getByText("取消")).toBeInTheDocument();
  });

  it("编辑模式点击取消回到默认状态", async () => {
    const user = userEvent.setup();
    render(<ChapterFeedback {...defaultProps} />);

    await user.click(screen.getByText("修改"));
    expect(screen.getByText("提交修改")).toBeInTheDocument();

    await user.click(screen.getByText("取消"));
    expect(screen.getByText("采纳")).toBeInTheDocument();
    expect(screen.getByText("修改")).toBeInTheDocument();
  });

  it("点击采纳调用 API 并显示已采纳", async () => {
    const api = (await import("@/lib/api")).default;
    const user = userEvent.setup();
    render(<ChapterFeedback {...defaultProps} />);

    await user.click(screen.getByText("采纳"));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/feedback", expect.objectContaining({
        project_id: 92,
        chapter_no: "1",
        action: "accept",
      }));
    });

    await waitFor(() => {
      expect(screen.getByText("✅ 已采纳")).toBeInTheDocument();
    });
  });

  it("已采纳状态可点击重新评价", async () => {
    const user = userEvent.setup();
    render(<ChapterFeedback {...defaultProps} />);

    await user.click(screen.getByText("采纳"));

    await waitFor(() => {
      expect(screen.getByText("✅ 已采纳")).toBeInTheDocument();
    });

    await user.click(screen.getByText("重新评价"));
    expect(screen.getByText("采纳")).toBeInTheDocument();
  });
});
