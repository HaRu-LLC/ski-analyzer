import "@testing-library/jest-dom";
import { render } from "@testing-library/react";
import { SkeletonOverlay } from "../SkeletonOverlay";
import type { FrameData } from "@/types/analysis";

const mockFrameData: FrameData = {
  frame_index: 0,
  timestamp_ms: 0,
  joint_positions_3d: {
    l_knee: [0.1, -0.5, 0.0],
    r_knee: [-0.1, -0.5, 0.0],
    l_hip: [0.1, -0.2, 0.0],
    r_hip: [-0.1, -0.2, 0.0],
    l_shoulder: [-0.2, 0.3, 0.0],
    r_shoulder: [0.2, 0.3, 0.0],
    neck: [0.0, 0.4, 0.0],
    head: [0.0, 0.5, 0.0],
  },
  joint_rotations: {},
  joint_angles: [
    {
      joint_name: "l_knee",
      joint_name_ja: "左膝",
      flexion: -55,
      rotation: 0,
      abduction: -5,
      confidence: "medium",
    },
    {
      joint_name: "l_shoulder",
      joint_name_ja: "左肩",
      flexion: 10,
      rotation: 0,
      abduction: 25,
      confidence: "high",
    },
  ],
};

describe("SkeletonOverlay", () => {
  it("renders canvas when visible with frameData", () => {
    const { container } = render(
      <SkeletonOverlay
        frameData={mockFrameData}
        width={1920}
        height={1080}
        visible={true}
      />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("returns null when not visible", () => {
    const { container } = render(
      <SkeletonOverlay
        frameData={mockFrameData}
        width={1920}
        height={1080}
        visible={false}
      />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeNull();
  });

  it("returns null when frameData is null", () => {
    const { container } = render(
      <SkeletonOverlay
        frameData={null}
        width={1920}
        height={1080}
        visible={true}
      />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeNull();
  });
});
