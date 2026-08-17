"""Command-line entry point for the scan mesh and Gaussian splat pipelines.

Usage
-----
  python run_pipeline.py mesh  --dataset DIR --output DIR [options]
  python run_pipeline.py splat --dataset DIR --output DIR [options]

Run with --help for full option list.
"""
import argparse
import logging
import sys


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='run_pipeline.py',
        description='Mobile LiDAR scan → X3D mesh and Gaussian splat pipelines',
    )
    sub = p.add_subparsers(dest='mode', required=True)

    # ---- shared arguments ------------------------------------------------
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument('--dataset',   required=True, metavar='DIR',
                        help='Path to scan dataset directory')
    shared.add_argument('--output',    required=True, metavar='DIR',
                        help='Output directory')
    shared.add_argument('--format',    default='x3d', metavar='FMT',
                        help='Output format (default: x3d)')
    shared.add_argument('--platform',  default='auto', metavar='NAME',
                        help='Scanner platform: navvis | metashape | meshroom | pix4d | colmap | e57 | auto (default: auto-detect)')
    shared.add_argument('--geo-csv',     default=None, metavar='FILE',
                        help='Geospatial survey CSV for georeferencing (optional)')
    shared.add_argument('--no-georef',   action='store_true',
                        help='Skip georeferencing even if --geo-csv is supplied')
    shared.add_argument('--epsg',      type=int, default=32605, metavar='INT',
                        help='Target projected CRS EPSG code (default: 32605 = UTM Zone 5N)')
    shared.add_argument('--verbose',   action='store_true',
                        help='Enable INFO logging')

    # ---- mesh subcommand -------------------------------------------------
    mesh = sub.add_parser('mesh', parents=[shared],
                          help='Textured polygon mesh pipeline')
    mesh.add_argument('--poisson-depth',    type=int,   default=9,    metavar='INT')
    mesh.add_argument('--atlas-size',       type=int,   default=4096, metavar='INT')
    mesh.add_argument('--colorise-stride',  type=int,   default=10,   metavar='INT')
    mesh.add_argument('--max-packets',      type=int,   default=6000, metavar='INT',
                      help='Max LiDAR packets decoded (6000 ≈ 1.15M points; use 0 for unlimited)')
    mesh.add_argument('--envmap-width',     type=int,   default=4096, metavar='INT')
    mesh.add_argument('--envmap-height',    type=int,   default=2048, metavar='INT')
    mesh.add_argument('--hdri-frame',       type=int,   default=None, metavar='INT',
                      help='Frame index for HDRI generation (default: auto)')

    # ---- splat subcommand ------------------------------------------------
    splat = sub.add_parser('splat', parents=[shared],
                           help='Gaussian splat pipeline')
    splat.add_argument('--image-size',    type=int,   default=512,    metavar='INT')
    splat.add_argument('--sh-degree',     type=int,   default=3,      metavar='INT')
    splat.add_argument('--iterations',    type=int,   default=10000,  metavar='INT')
    splat.add_argument('--frame-stride',  type=int,   default=5,      metavar='INT')
    splat.add_argument('--init-points',   type=int,   default=100000, metavar='INT')
    splat.add_argument('--decode-sh',     action='store_true',
                       help='Pre-decode SH coefficients to RGB in PLY output (for consumers without SH support)')

    # ---- convert subcommand ---------------------------------------------
    conv = sub.add_parser('convert',
                          help='Convert a Gaussian splat file between formats')
    conv.add_argument('--input',      required=True, metavar='FILE',
                      help='Source file (.ply, .splat, .glb, .x3d, .x3dv, .x3dj)')
    conv.add_argument('--output',     required=True, metavar='DIR',
                      help='Output directory')
    conv.add_argument('--stem',       default=None,  metavar='NAME',
                      help='Output filename stem (default: source stem)')
    conv.add_argument('--format',     required=True, metavar='FMT',
                      help='Target format: ply | splat | glb | x3d | x3dv | x3dj')
    conv.add_argument('--sh-degree',  type=int, default=None, metavar='INT',
                      help='Override SH degree in output (default: match source)')
    conv.add_argument('--decode-sh',  action='store_true',
                      help='Pre-decode SH DC to RGB (for viewers without SH decoding)')
    conv.add_argument('--verbose',    action='store_true',
                      help='Enable INFO logging')

    # ---- folder-splat subcommand -----------------------------------------
    fs = sub.add_parser('folder-splat',
                        help='COLMAP SfM + 3DGS pipeline for a plain image folder')
    fs.add_argument('--images',       required=True,  metavar='DIR',
                    help='Folder containing only the input images')
    fs.add_argument('--output',       required=True,  metavar='DIR',
                    help='Output directory')
    fs.add_argument('--format',       default='x3d',  metavar='FMT',
                    help='Export format: x3d | x3dv | x3dj | ply | splat | glb (default: x3d)')
    fs.add_argument('--focal-px',     type=float,     default=None, metavar='FLOAT',
                    help='Camera focal length in pixels (auto-extracted from EXIF if omitted)')
    fs.add_argument('--image-size',   type=int,       default=512,  metavar='INT')
    fs.add_argument('--sh-degree',    type=int,       default=3,    metavar='INT')
    fs.add_argument('--iterations',   type=int,       default=10000,metavar='INT')
    fs.add_argument('--matcher',      default='exhaustive', metavar='NAME',
                    help='COLMAP matcher: exhaustive | sequential (default: exhaustive)')
    fs.add_argument('--frame-stride', type=int,       default=1,    metavar='INT',
                    help='Use every N-th registered image for training (default: 1 = all)')
    fs.add_argument('--decode-sh',    action='store_true')
    fs.add_argument('--colmap-bin',   default='colmap', metavar='PATH',
                    help='colmap binary path (used when pycolmap is not installed)')    fs.add_argument('--turntable',    action='store_true',
                    help='Use synthetic circular poses (bypass COLMAP mapper) — recommended for turntable captures')    fs.add_argument('--verbose',      action='store_true')

    return p


def main() -> None:
    args = _build_parser().parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format='%(levelname)s %(name)s %(message)s',
        stream=sys.stdout,
    )

    # folder-splat — no dataset/georef needed, handle early
    if args.mode == 'folder-splat':
        from rawkee.tools.lidar import FolderSplatPipeline
        out = FolderSplatPipeline(
            image_size      = args.image_size,
            sh_degree       = args.sh_degree,
            iterations      = args.iterations,
            matcher         = args.matcher,
            turntable_mode  = args.turntable,
            colmap_bin      = args.colmap_bin,
        ).run(
            image_dir     = args.images,
            output_dir    = args.output,
            output_format = args.format,
            focal_px      = args.focal_px,
            decode_sh     = args.decode_sh,
            frame_stride  = args.frame_stride,
        )
        print(f'Saved: {out}')
        return

    # convert subcommand has no dataset/georef — handle it early
    if args.mode == 'convert':
        from pathlib import Path as _Path
        from rawkee.tools.lidar import convert_splat
        in_path = _Path(args.input)
        stem    = args.stem or in_path.stem
        out     = convert_splat(
            input_path = in_path,
            output_dir = args.output,
            stem       = stem,
            fmt        = args.format,
            sh_degree  = args.sh_degree,
            decode_sh  = args.decode_sh,
        )
        print(f'Converted: {out}')
        return

    from rawkee.tools.lidar import ScanDataset

    dataset = ScanDataset(args.dataset, platform=args.platform)

    # Resolve georeferencing: warn and fall back if CSV is missing or suppressed
    effective_csv = None
    if args.geo_csv and not args.no_georef:
        from pathlib import Path as _Path
        _csv = _Path(args.geo_csv)
        if _csv.exists():
            effective_csv = _csv
        else:
            logging.getLogger(__name__).warning(
                'Trimble CSV not found: %s — proceeding without georeferencing', _csv
            )

    if args.mode == 'mesh':
        from rawkee.tools.lidar import MeshPipeline
        MeshPipeline(
            poisson_depth=args.poisson_depth,
            atlas_size=args.atlas_size,
            colorise_stride=args.colorise_stride,
            max_packets=args.max_packets if args.max_packets > 0 else 10_000_000,
        ).run(
            dataset,
            output_dir=args.output,
            output_format=args.format,
            hdri_frame=args.hdri_frame,
            envmap_width=args.envmap_width,
            envmap_height=args.envmap_height,
            trimble_csv=effective_csv,
            georef_epsg=args.epsg,
        )

    elif args.mode == 'splat':
        from rawkee.tools.lidar import SplatPipeline
        SplatPipeline(
            image_size=args.image_size,
            sh_degree=args.sh_degree,
            iterations=args.iterations,
            frame_stride=args.frame_stride,
            init_points=args.init_points,
        ).run(
            dataset,
            output_dir=args.output,
            output_format=args.format,
            trimble_csv=effective_csv,
            georef_epsg=args.epsg,
            decode_sh=args.decode_sh,
        )


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as exc:
        print(f'\nFATAL: {exc}', flush=True)
        sys.exit(1)
