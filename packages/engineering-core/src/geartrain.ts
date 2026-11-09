/**
 * Gear train calculator: chain of gear meshes.
 * Overall ratio, torque multiplication, efficiency, output speed.
 */
import { GearParams, meshGears } from './gears.js';
import { assertPositive } from './units.js';

export interface GearTrainStage {
  driver: GearParams;
  driven: GearParams;
  /** Mesh efficiency (default 0.98 external, 0.95 worm — Estimated). */
  efficiency?: number;
}

export interface GearTrainResult {
  overallRatio: number; // omega_in / omega_out
  outputSpeedRadps: number;
  outputTorqueNm: number;
  totalEfficiency: number;
  stageRatios: number[];
  stageOutputs: { speedRadps: number; torqueNm: number }[];
  warnings: string[];
  resultType: 'Calculated';
}

export function calculateGearTrain(
  stages: GearTrainStage[],
  inputSpeedRadps: number,
  inputTorqueNm: number
): GearTrainResult {
  if (stages.length === 0) throw new Error('Gear train needs at least one stage');
  assertPositive('inputSpeed', inputSpeedRadps);
  assertPositive('inputTorque', inputTorqueNm);

  let speed = inputSpeedRadps;
  let torque = inputTorqueNm;
  let totalEff = 1;
  const stageRatios: number[] = [];
  const stageOutputs: { speedRadps: number; torqueNm: number }[] = [];
  const warnings: string[] = [];

  for (let i = 0; i < stages.length; i++) {
    const st = stages[i];
    const mesh = meshGears(st.driver, st.driven, {
      inputSpeedRadps: speed,
      inputTorqueNm: torque
    });
    const eff = st.efficiency ?? (st.driver.type === 'worm' ? 0.7 : 0.98);
    speed = mesh.outputSpeedRadps;
    torque = (torque * mesh.ratio * eff) / 1; // torque multiplies by ratio (speed reduces)
    // Correct: T_out = T_in * ratio * eff where ratio = omega_in/omega_out
    totalEff *= eff;
    stageRatios.push(mesh.ratio);
    stageOutputs.push({ speedRadps: speed, torqueNm: torque });
    for (const w of mesh.warnings) warnings.push(`Stage ${i + 1}: ${w}`);
  }

  const overallRatio = inputSpeedRadps / speed;
  return {
    overallRatio,
    outputSpeedRadps: speed,
    outputTorqueNm: torque,
    totalEfficiency: totalEff,
    stageRatios,
    stageOutputs,
    warnings,
    resultType: 'Calculated'
  };
}
