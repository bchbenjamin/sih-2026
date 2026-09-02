from types import SimpleNamespace


def test_bbox_covers_request_allows_half_pixel_tolerance():
    bounds = SimpleNamespace(left=79.5498611111455, bottom=30.300138888884955,
                            right=79.89986111114555, top=30.500138888884983)
    requested = (79.55, 30.30, 79.90, 30.50)
    resolution = (0.0002777777777778146, 0.0002777777777778146)

    from scripts.phase1.download_dem import bbox_covers_request

    assert bbox_covers_request(bounds, requested, resolution) is True
