/**
 * MapPage — Full-page map view within the Dashboard.
 *
 * The map occupies the entire content area of the dashboard layout.
 */
import { MapComponent } from '@/features/map/components/MapComponent';

export function MapPage() {
  return (
    <div className="h-full w-full">
      <MapComponent />
    </div>
  );
}
