import { useEffect, useState, type DependencyList } from 'react';

export interface AsyncState<T> {
  data?: T;
  loading: boolean;
  error?: Error;
  reload: () => void;
}

// Minimal data loader with loading/error state and a reload trigger. Guards
// against setting state after unmount.
export function useAsync<T>(fn: () => Promise<T>, deps: DependencyList = []): AsyncState<T> {
  const [state, setState] = useState<{ data?: T; loading: boolean; error?: Error }>({
    loading: true,
  });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let live = true;
    setState({ loading: true });
    fn()
      .then((d) => live && setState({ data: d, loading: false }))
      .catch((e) => live && setState({ error: e as Error, loading: false }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { ...state, reload: () => setTick((t) => t + 1) };
}
