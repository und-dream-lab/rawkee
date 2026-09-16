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
                        help='Path to scan dataset: NavVis folder, Metashape .psx/.psz, Meshroom .mg, Pix4D .p4d, COLMAP sparse folder, or .e57 file')
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
    mesh.add_argument('--max-packets',      type=int,   default=0,    metavar='INT',
                      help='Max LiDAR packets decoded per sensor (0 = unlimited/full scan; '
                           'set a small value like 6000 only for quick iteration on a partial scan)')
    mesh.add_argument('--quick',            action='store_true',
                      help='Quick validation mode: uses aggressive downsampling, reduced Poisson depth, '
                           'and skips heavy processing to verify pipeline correctness quickly')
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
    fs.add_argument('--image-size',   type=int,       default=1024, metavar='INT',
                    help='Training image resolution in pixels (default: 1024)')
    fs.add_argument('--sh-degree',    type=int,       default=3,    metavar='INT')
    fs.add_argument('--iterations',   type=int,       default=30000,metavar='INT',
                    help='3DGS training iterations (default: 30000)')
    fs.add_argument('--matcher',      default='exhaustive-hloc', metavar='NAME',
                    help='Feature matcher: exhaustive-hloc | sequential-hloc | exhaustive | sequential')
    fs.add_argument('--frame-stride', type=int,       default=1,    metavar='INT',
                    help='Use every N-th registered image for training (default: 1 = all)')
    fs.add_argument('--turntable',    action='store_true',
                    help='Use synthetic circular poses — recommended for turntable captures')
    fs.add_argument('--n-sets',       type=int,       default=1,    metavar='INT',
                    help='Number of distinct turntable passes (default: 1)')
    fs.add_argument('--turntable-elevation', type=float, default=0.0, metavar='DEG',
                    help='Camera elevation override in degrees (0 = auto-estimate from COLMAP)')
    fs.add_argument('--turntable-radius',    type=float, default=0.0, metavar='M',
                    help='Camera-to-object distance override in metres (0 = auto-estimate)')
    fs.add_argument('--masks-dir',    default=None,   metavar='DIR',
                    help='Folder of pre-made mask images (white=foreground)')
    fs.add_argument('--auto-mask',    action='store_true',
                    help='Auto-generate masks using rembg AI model')
    fs.add_argument('--chroma-rgb',   type=float,     nargs=3,      default=None, metavar=('R', 'G', 'B'),
                    help='Background colour for chroma-key masking (e.g. 0 80 180 for blue)')
    fs.add_argument('--chroma-tolerance', type=float, default=30.0, metavar='DEG',
                    help='Hue tolerance for chroma-key masking (default: 30)')
    fs.add_argument('--mask-erosion-px',  type=int,   default=8,    metavar='INT',
                    help='Shrink masks inward by this many pixels (default: 8; 0 = disable)')
    fs.add_argument('--densify-until',    type=int,   default=0,    metavar='INT',
                    help='Step at which Gaussian growth stops (0 = auto = iterations//2)')
    fs.add_argument('--densify-every',    type=int,   default=100,  metavar='INT',
                    help='Run density control every N steps (default: 100)')
    fs.add_argument('--opacity-reset-every', type=int, default=0,   metavar='INT',
                    help='Reset opacities every N steps (0 = never; paper default: 3000)')
    fs.add_argument('--grad-thresh-mult', type=float, default=1.5,  metavar='FLOAT',
                    help='Gradient threshold multiplier for split/clone decisions (default: 1.5)')
    fs.add_argument('--grad-mode',    default='2d',   metavar='MODE',
                    help='Density gradient mode: 2d (screen-space) | 3d (world-space) (default: 2d)')
    fs.add_argument('--decode-sh',    action='store_true')
    fs.add_argument('--colmap-only',  action='store_true',
                    help='Run COLMAP + mask generation only; skip 3DGS training')
    fs.add_argument('--colmap-bin',   default='colmap', metavar='PATH',
                    help='colmap binary path (used when pycolmap is not installed)')
    fs.add_argument('--verbose',      action='store_true')

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
        from pathlib import Path as _Path
        _use_hloc = 'hloc' in args.matcher
        _matcher  = 'exhaustive' if 'exhaustive' in args.matcher else 'sequential'
        _hloc_win = 0 if 'exhaustive' in args.matcher else 10
        out = FolderSplatPipeline(
            image_size              = args.image_size,
            sh_degree               = args.sh_degree,
            iterations              = args.iterations,
            matcher                 = _matcher,
            turntable_mode          = args.turntable,
            n_sets                  = args.n_sets,
            turntable_elevation_deg = args.turntable_elevation,
            turntable_radius        = args.turntable_radius,
            masks_dir               = _Path(args.masks_dir) if args.masks_dir else None,
            auto_mask               = args.auto_mask,
            chroma_rgb              = tuple(args.chroma_rgb) if args.chroma_rgb else None,
            chroma_tolerance        = args.chroma_tolerance,
            mask_erosion_px         = args.mask_erosion_px,
            opacity_reset_every     = args.opacity_reset_every,
            hloc_window             = _hloc_win,
            densify_every           = args.densify_every,
            grad_thresh_mult        = args.grad_thresh_mult,
            use_hloc                = _use_hloc,
            colmap_bin              = args.colmap_bin,
        ).run(
            image_dir         = args.images,
            output_dir        = args.output,
            output_format     = args.format,
            focal_px          = args.focal_px,
            decode_sh         = args.decode_sh,
            frame_stride      = args.frame_stride,
            densify_grad_mode = args.grad_mode,
            densify_until     = args.densify_until,
            colmap_only       = args.colmap_only,
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
            quick=args.quick,
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
