use std::fs::File;
use std::io::{Write, BufWriter};
use std::path::PathBuf;
use rand::Rng;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct Config {
    #[serde(rename = "G")]
    g: f64,
    #[serde(rename = "EPS")]
    eps: f64,
    #[serde(rename = "DT")]
    dt: f64,
    #[serde(rename = "STEPS")]
    steps: usize,
    #[serde(rename = "N")]
    n: usize,
    #[serde(rename = "OUTPUT_RS_SEQ")]
    output_file: String,
}

fn load_config() -> Config {
    let mut config_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    config_path.push("../../config/config.json");
    
    let config_str = std::fs::read_to_string(&config_path)
        .expect("Failed to read config file");
    
    serde_json::from_str(&config_str)
        .expect("Failed to parse config file")
}

#[derive(Clone)]
struct Body {
    pos: [f64; 3],
    vel: [f64; 3],
    mass: f64,
}

fn compute_forces(bodies: &Vec<Body>, g: f64, eps: f64) -> Vec<[f64; 3]> {
    let n = bodies.len();
    let mut forces = vec![[0.0; 3]; n];

    for i in 0..n {
        for j in 0..n {
            if i == j {
                continue;
            }

            let dx = bodies[j].pos[0] - bodies[i].pos[0];
            let dy = bodies[j].pos[1] - bodies[i].pos[1];
            let dz = bodies[j].pos[2] - bodies[i].pos[2];

            let dist_sqr = dx*dx + dy*dy + dz*dz + eps*eps;
            let inv_dist3 = 1.0 / dist_sqr.powf(1.5);

            let f = g * bodies[i].mass * bodies[j].mass * inv_dist3;

            forces[i][0] += f * dx;
            forces[i][1] += f * dy;
            forces[i][2] += f * dz;
        }
    }

    forces
}

fn main() {
    let config = load_config();
    
    // inicijalizacija tela (nasumične pozicije)
    let mut rng = rand::thread_rng();
    let mut bodies: Vec<Body> = (0..config.n)
        .map(|_| Body {
            pos: [
                rng.gen_range(0.0..1.0),
                rng.gen_range(0.0..1.0),
                rng.gen_range(0.0..1.0),
            ],
            vel: [0.0, 0.0, 0.0],
            mass: 1.0,
        })
        .collect();

    let file = File::create(&config.output_file).unwrap();
    let mut writer = BufWriter::new(file);

    writeln!(writer, "iteration,body_id,x,y,z").unwrap();

    for step in 0..config.steps {

        let forces = compute_forces(&bodies, config.g, config.eps);

        // Euler integracija
        for i in 0..config.n {
            let ax = forces[i][0] / bodies[i].mass;
            let ay = forces[i][1] / bodies[i].mass;
            let az = forces[i][2] / bodies[i].mass;

            bodies[i].vel[0] += ax * config.dt;
            bodies[i].vel[1] += ay * config.dt;
            bodies[i].vel[2] += az * config.dt;

            bodies[i].pos[0] += bodies[i].vel[0] * config.dt;
            bodies[i].pos[1] += bodies[i].vel[1] * config.dt;
            bodies[i].pos[2] += bodies[i].vel[2] * config.dt;
        }

        // zapis CSV
        for i in 0..config.n {
            writeln!(
                writer,
                "{},{},{},{},{}",
                step,
                i,
                bodies[i].pos[0],
                bodies[i].pos[1],
                bodies[i].pos[2]
            ).unwrap();
        }
    }

    println!("Simulation finished.");
}
