use std::env;
use std::error::Error;
use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::Command;

use csv::ReaderBuilder;
use plotters::prelude::*;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Record {
    iteration: u32,
    body_id: u32,
    x: f64,
    y: f64,
    z: f64,
}

fn run() -> Result<(), Box<dyn Error>> {

    let args: Vec<String> = env::args().collect();

    // Jednostavan mod: visualization <csv_base_name>
    // npr. visualization seq_rust  -> koristi outputs/seq_rust.csv i pravi animations/seq_rust.gif
    if args.len() == 2 {
        let base = &args[1];

        // workspace root: .../n-body-problem iz CARGO_MANIFEST_DIR = .../rust/visualization
        let mut root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        root.pop(); // visualization
        root.pop(); // rust

        let outputs_dir = root.join("outputs");
        let animations_dir = root.join("animations");
        fs::create_dir_all(&animations_dir)?;

        // ako korisnik da seq_rust.csv, skini ekstenziju za bazno ime
        let base_name = Path::new(base)
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or(base);

        let csv_name = if base.ends_with(".csv") {
            base.to_string()
        } else {
            format!("{}.csv", base)
        };

        let input_path = outputs_dir.join(csv_name);
        if !input_path.exists() {
            eprintln!("CSV not found: {}", input_path.display());
            std::process::exit(1);
        }

        // Učitaj podatke
        let file = File::open(&input_path)?;
        let mut reader = ReaderBuilder::new()
            .has_headers(true)
            .from_reader(file);

        let mut records: Vec<Record> = Vec::new();
        for result in reader.deserialize() {
            let record: Record = result?;
            records.push(record);
        }

        if records.is_empty() {
            eprintln!("Input CSV is empty: {}", input_path.display());
            return Ok(());
        }

        // Globalne granice i max iteracija
        let mut min_x = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        let mut max_iter = 0u32;

        for r in &records {
            if r.x < min_x {
                min_x = r.x;
            }
            if r.x > max_x {
                max_x = r.x;
            }
            if r.y < min_y {
                min_y = r.y;
            }
            if r.y > max_y {
                max_y = r.y;
            }
            if r.iteration > max_iter {
                max_iter = r.iteration;
            }
        }

        if (max_x - min_x).abs() < 1e-9 {
            min_x -= 1.0;
            max_x += 1.0;
        }
        if (max_y - min_y).abs() < 1e-9 {
            min_y -= 1.0;
            max_y += 1.0;
        }

        // Generiši PNG frejmove u animations sa prefiksom <base_name>_frame_XXXXX.png
        use std::collections::BTreeMap;

        let mut by_iter: BTreeMap<u32, BTreeMap<u32, (f64, f64)>> =
            BTreeMap::new();
        for r in &records {
            by_iter
                .entry(r.iteration)
                .or_default()
                .insert(r.body_id, (r.x, r.y));
        }

        let palette = Palette99::pick;
        let step: u32 = 1;

        for iter in (0..=max_iter).step_by(step as usize) {
            if let Some(bodies) = by_iter.get(&iter) {
                let file_name = format!("{}_frame_{:05}.png", base_name, iter);
                let frame_path = animations_dir.join(&file_name);

                let root = BitMapBackend::new(
                    frame_path.to_str().unwrap(),
                    (1280, 720),
                )
                .into_drawing_area();
                root.fill(&WHITE)?;

                let mut chart = ChartBuilder::on(&root)
                    .margin(20)
                    .caption(
                        format!(
                            "Iteration {}",
                            iter
                        ),
                        ("sans-serif", 30),
                    )
                    .x_label_area_size(40)
                    .y_label_area_size(60)
                    .build_cartesian_2d(min_x..max_x, min_y..max_y)?;

                chart.configure_mesh().draw()?;

                for (idx, (_body_id, (x, y))) in bodies.iter().enumerate() {
                    let color = palette(idx);
                    chart.draw_series(std::iter::once(Circle::new(
                        (*x, *y),
                        3,
                        color.filled(),
                    )))?;
                }

                root.present()?;
            }
        }

        // Pozovi ffmpeg da generiše GIF iz frejmova
        let gif_name = format!("{}.gif", base_name);

        // prvo paleta
        let status = Command::new("ffmpeg")
            .current_dir(&animations_dir)
            .args([
                "-y",
                "-framerate",
                "10",
                "-i",
                &format!("{}_frame_%05d.png", base_name),
                "-vf",
                "palettegen",
                "palette.png",
            ])
            .status()?;

        if !status.success() {
            eprintln!("ffmpeg palettegen failed with status: {}", status);
            std::process::exit(1);
        }

        let status = Command::new("ffmpeg")
            .current_dir(&animations_dir)
            .args([
                "-y",
                "-framerate",
                "10",
                "-i",
                &format!("{}_frame_%05d.png", base_name),
                "-i",
                "palette.png",
                "-lavfi",
                "paletteuse",
                "-loop",
                "0",
                &gif_name,
            ])
            .status()?;

        if !status.success() {
            eprintln!("ffmpeg gif generation failed with status: {}", status);
            std::process::exit(1);
        }

        // Obriši privremene fajlove: sve PNG frejmove i palette.png
        for iter in (0..=max_iter).step_by(step as usize) {
            if by_iter.contains_key(&iter) {
                let frame_path =
                    animations_dir.join(format!("{}_frame_{:05}.png", base_name, iter));
                let _ = fs::remove_file(frame_path);
            }
        }
        let _ = fs::remove_file(animations_dir.join("palette.png"));

        println!(
            "GIF generated at {}/{}",
            animations_dir.display(),
            gif_name
        );

        return Ok(());
    }

    // Napredni modovi iz prethodne verzije (trajectories / frames)
    if args.len() < 3 {
        eprintln!("Usage:");
        eprintln!("  visualization <input.csv> trajectories <output.svg>");
        eprintln!("  visualization <input.csv> frames <output_prefix> [step]");
        eprintln!("  or: visualization <csv_base_name>   # auto GIF in animations/");
        std::process::exit(1);
    }

    let input_path = &args[1];
    let mode = &args[2];

    let file = File::open(input_path)?;
    let mut reader = ReaderBuilder::new()
        .has_headers(true)
        .from_reader(file);

    let mut records: Vec<Record> = Vec::new();
    for result in reader.deserialize() {
        let record: Record = result?;
        records.push(record);
    }

    if records.is_empty() {
        eprintln!("Input CSV is empty: {}", input_path);
        return Ok(());
    }

    // Izračunaj globalne min/max da svi frejmovi imaju istu skalu
    let mut min_x = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut min_y = f64::INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    let mut max_iter = 0u32;

    for r in &records {
        if r.x < min_x {
            min_x = r.x;
        }
        if r.x > max_x {
            max_x = r.x;
        }
        if r.y < min_y {
            min_y = r.y;
        }
        if r.y > max_y {
            max_y = r.y;
        }
        if r.iteration > max_iter {
            max_iter = r.iteration;
        }
    }

    if (max_x - min_x).abs() < 1e-9 {
        min_x -= 1.0;
        max_x += 1.0;
    }
    if (max_y - min_y).abs() < 1e-9 {
        min_y -= 1.0;
        max_y += 1.0;
    }

    match mode.as_str() {
        "trajectories" => {
            // očekuje se: visualization input.csv trajectories output.svg
            let output_path = if args.len() >= 4 {
                &args[3]
            } else {
                "output.svg"
            };

            use std::collections::BTreeMap;

            let mut by_body: BTreeMap<u32, Vec<(f64, f64)>> = BTreeMap::new();
            for r in &records {
                by_body
                    .entry(r.body_id)
                    .or_default()
                    .push((r.x, r.y));
            }

            let root =
                SVGBackend::new(output_path, (1280, 720)).into_drawing_area();
            root.fill(&WHITE)?;

            let mut chart = ChartBuilder::on(&root)
                .margin(20)
                .caption(
                    format!("N-body trajectories ({})", input_path),
                    ("sans-serif", 30),
                )
                .x_label_area_size(40)
                .y_label_area_size(60)
                .build_cartesian_2d(min_x..max_x, min_y..max_y)?;

            chart.configure_mesh().draw()?;

            let palette = Palette99::pick;

            for (idx, (body_id, points)) in by_body.iter().enumerate() {
                let color = palette(idx);
                let legend_style = ShapeStyle::from(&color);

                chart
                    .draw_series(LineSeries::new(points.clone(), &color))?
                    .label(format!("body {}", body_id))
                    .legend(move |(x, y)| {
                        PathElement::new(
                            vec![(x, y), (x + 20, y)],
                            legend_style.clone(),
                        )
                    });

                chart.draw_series(points.iter().map(|(x, y)| {
                    Circle::new((*x, *y), 2, color.filled())
                }))?;
            }

            chart
                .configure_series_labels()
                .background_style(&WHITE.mix(0.8))
                .border_style(&BLACK)
                .draw()?;

            root.present()?;

            println!("Trajectories written to {}", output_path);
        }
        "frames" => {
            // očekuje se: visualization input.csv frames prefix [step]
            if args.len() < 4 {
                eprintln!("Mode 'frames' requires <output_prefix> argument");
                std::process::exit(1);
            }
            let prefix = &args[3];
            let step: u32 = if args.len() >= 5 {
                args[4].parse().unwrap_or(1)
            } else {
                1
            };

            use std::collections::BTreeMap;

            // Pregrupiši po iteracijama: iteration -> body_id -> (x,y)
            let mut by_iter: BTreeMap<u32, BTreeMap<u32, (f64, f64)>> =
                BTreeMap::new();
            for r in &records {
                by_iter
                    .entry(r.iteration)
                    .or_default()
                    .insert(r.body_id, (r.x, r.y));
            }

            let palette = Palette99::pick;

            for iter in (0..=max_iter).step_by(step as usize) {
                if let Some(bodies) = by_iter.get(&iter) {
                    let filename =
                        format!("{}_{:05}.svg", prefix, iter);
                    let root = SVGBackend::new(
                        &filename,
                        (1280, 720),
                    )
                    .into_drawing_area();
                    root.fill(&WHITE)?;

                    let mut chart = ChartBuilder::on(&root)
                        .margin(20)
                        .caption(
                            format!("Iteration {} ({})", iter, input_path),
                            ("sans-serif", 30),
                        )
                        .x_label_area_size(40)
                        .y_label_area_size(60)
                        .build_cartesian_2d(min_x..max_x, min_y..max_y)?;

                    chart.configure_mesh().draw()?;

                    for (idx, (body_id, (x, y))) in bodies.iter().enumerate() {
                        let color = palette(idx);
                        chart.draw_series(std::iter::once(Circle::new(
                            (*x, *y),
                            3,
                            color.filled(),
                        )))?
                        .label(format!("body {}", body_id));
                    }

                    chart
                        .configure_series_labels()
                        .background_style(&WHITE.mix(0.8))
                        .border_style(&BLACK)
                        .draw()?;

                    root.present()?;
                }
            }

            println!(
                "Frames written with prefix '{}' (step = {})",
                prefix, step
            );
        }
        other => {
            eprintln!("Unknown mode: {}", other);
            eprintln!("Use 'trajectories' or 'frames'");
            std::process::exit(1);
        }
    }

    Ok(())
}

fn main() {
    if let Err(err) = run() {
        eprintln!("Error: {}", err);
        std::process::exit(1);
    }
}
