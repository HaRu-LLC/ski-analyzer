import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { IdealComparison } from "../IdealComparison";
import type { IdealComparison as IdealComparisonType } from "@/types/analysis";

const mockComparisons: IdealComparisonType[] = [
  {
    joint_name: "l_knee",
    joint_name_ja: "左膝",
    user_angle: -50.0,
    ideal_angle: -55.0,
    difference: 5.0,
    rating: "good",
  },
  {
    joint_name: "r_knee",
    joint_name_ja: "右膝",
    user_angle: -40.0,
    ideal_angle: -55.0,
    difference: 15.0,
    rating: "needs_improvement",
  },
  {
    joint_name: "l_hip",
    joint_name_ja: "左股関節",
    user_angle: -10.0,
    ideal_angle: -45.0,
    difference: 35.0,
    rating: "poor",
  },
];

describe("IdealComparison", () => {
  it("renders comparison table with all joints", () => {
    render(<IdealComparison comparisons={mockComparisons} />);
    expect(screen.getByText("左膝")).toBeInTheDocument();
    expect(screen.getByText("右膝")).toBeInTheDocument();
    expect(screen.getByText("左股関節")).toBeInTheDocument();
  });

  it("displays user and ideal angles", () => {
    render(<IdealComparison comparisons={mockComparisons} />);
    expect(screen.getByText("-50.0°")).toBeInTheDocument();
    // -55.0° は複数行 (左膝・右膝の理想値) に出現するため getAllByText を使用
    expect(screen.getAllByText("-55.0°").length).toBeGreaterThanOrEqual(1);
  });

  it("shows difference values", () => {
    render(<IdealComparison comparisons={mockComparisons} />);
    expect(screen.getByText("5.0°")).toBeInTheDocument();
    expect(screen.getByText("15.0°")).toBeInTheDocument();
  });

  it("color-codes ratings visually", () => {
    render(<IdealComparison comparisons={mockComparisons} />);
    // good, needs_improvement, poor の表示がそれぞれ存在する
    expect(screen.getByText("良好")).toBeInTheDocument();
    expect(screen.getByText("改善余地")).toBeInTheDocument();
    expect(screen.getByText("要改善")).toBeInTheDocument();
  });

  it("renders empty state when no comparisons", () => {
    render(<IdealComparison comparisons={[]} />);
    expect(screen.getByText(/比較データ/i)).toBeInTheDocument();
  });
});
