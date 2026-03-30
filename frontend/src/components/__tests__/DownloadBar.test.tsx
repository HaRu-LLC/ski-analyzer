import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { DownloadBar } from "../DownloadBar";

describe("DownloadBar", () => {
  it("renders links only for available artifacts", () => {
    render(
      <DownloadBar
        analysisId="test-id"
        artifacts={{ video: false, report: true, csv: true }}
      />
    );

    const reportLink = screen.getByRole("link", { name: /レポート/i });
    const csvLink = screen.getByRole("link", { name: /数値データ/i });

    expect(reportLink).toHaveAttribute("href", "http://localhost:8000/api/download/test-id/report");
    expect(csvLink).toHaveAttribute("href", "http://localhost:8000/api/download/test-id/csv");
    expect(screen.getByText(/解析動画/)).toHaveAttribute("aria-disabled", "true");
  });
});
