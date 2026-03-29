import { useCallback, useRef, useState } from "react";

type PlaybackSpeed = 0.25 | 0.5 | 1 | 2;

interface UseVideoPlayerOptions {
  totalFrames: number;
  fps: number;
}

/**
 * 動画再生制御フック.
 *
 * コマ送り、再生速度変更、フレーム同期を管理する。
 */
export function useVideoPlayer({ totalFrames, fps }: UseVideoPlayerOptions) {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<PlaybackSpeed>(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const play = useCallback(() => {
    setPlaying(true);
  }, []);

  const pause = useCallback(() => {
    setPlaying(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const togglePlay = useCallback(() => {
    if (playing) pause();
    else play();
  }, [playing, play, pause]);

  const stepForward = useCallback(() => {
    setCurrentFrame((prev) => Math.min(totalFrames - 1, prev + 1));
  }, [totalFrames]);

  const stepBackward = useCallback(() => {
    setCurrentFrame((prev) => Math.max(0, prev - 1));
  }, []);

  const seekTo = useCallback(
    (frame: number) => {
      setCurrentFrame(Math.max(0, Math.min(totalFrames - 1, frame)));
    },
    [totalFrames]
  );

  const changeSpeed = useCallback((newSpeed: PlaybackSpeed) => {
    setSpeed(newSpeed);
  }, []);

  return {
    currentFrame,
    playing,
    speed,
    play,
    pause,
    togglePlay,
    stepForward,
    stepBackward,
    seekTo,
    changeSpeed,
    setCurrentFrame,
  };
}
