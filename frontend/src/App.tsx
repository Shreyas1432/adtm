import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { Connections } from './screens/Connections';
import { SchemaDiscovery } from './screens/SchemaDiscovery';
import { Extraction } from './screens/Extraction';
import { DataQuality } from './screens/DataQuality';
import { Mapping } from './screens/Mapping';
import { LoadReconcile } from './screens/LoadReconcile';
import { Audit } from './screens/Audit';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/connections" replace />} />
        <Route path="/connections" element={<Connections />} />
        <Route path="/discovery" element={<SchemaDiscovery />} />
        <Route path="/extraction" element={<Extraction />} />
        <Route path="/dq" element={<DataQuality />} />
        <Route path="/mapping" element={<Mapping />} />
        <Route path="/load" element={<LoadReconcile />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="*" element={<Navigate to="/connections" replace />} />
      </Route>
    </Routes>
  );
}
