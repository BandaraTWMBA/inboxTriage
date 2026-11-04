import { useCallback, useEffect, useRef, useState } from "react";

// Small data-loading hook. `reload({ silent: true })` refetches without flipping `loading`.
// A 401 from any call tells the auth layer the session is gone.
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const seq = useRef(0);

  const run = useCallback(async (opts = {}) => {
    const mine = ++seq.current;
    if (!opts.silent) setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fnRef.current();
      if (mine === seq.current) setState({ data, error: null, loading: false });
    } catch (e) {
      if (e?.status === 401) window.dispatchEvent(new Event("it:unauthorized"));
      if (mine === seq.current) setState((s) => ({ ...s, error: e, loading: false }));
    }
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { run(); }, deps);

  const setData = useCallback(
    (updater) =>
      setState((s) => ({ ...s, data: typeof updater === "function" ? updater(s.data) : updater })),
    []
  );

  return { ...state, reload: run, setData };
}
