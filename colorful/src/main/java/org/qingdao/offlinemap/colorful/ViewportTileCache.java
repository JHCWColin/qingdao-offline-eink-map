package org.qingdao.offlinemap.colorful;

import org.mapsforge.map.layer.cache.InMemoryTileCache;
import org.mapsforge.map.layer.queue.Job;

import java.util.Set;

/** Keeps every tile of the actual render buffer resident, including its offscreen margin. */
public final class ViewportTileCache extends InMemoryTileCache {
    public ViewportTileCache() {
        super(24);
    }

    @Override public synchronized void setWorkingSet(Set<Job> jobs) {
        // TileLayer clears and rebuilds each frame. Evicting a visible tile before the
        // remaining tiles finish causes an endless render/evict/redraw cycle.
        // Allow a second viewport for panning and jobs completing from the previous view.
        int required = Math.max(24, jobs.size() * 2);
        if (required > getCapacity()) setCapacity(required);
        super.setWorkingSet(jobs);
    }
}
