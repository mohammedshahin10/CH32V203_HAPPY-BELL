# Pending Tasks

This file contains unfinished work only. Earlier peripheral test results are
recorded in `PROGRESS.md`. The default complete cooperative application now
fits the G8R6 Flash and RAM regions. Maximum-volume plain/ENC quality,
playback counters, integrated hardware flow, astronomy timing, and electrical
timing remain to be verified.

## Build and Target Validation

- [ ] Flash the clean 2026-09-05 default full-profile image and confirm `Loading...`
  advances to the reference idle/date display after the 600 ms service
  interval; then run the complete menu, schedule, Panchang, and audio flow on
  CH32V203G8R6 hardware. The clean ELF has a strong `TIM3_IRQHandler` and its
  vector entry points to that handler; the remaining check requires hardware.
- [ ] Inspect the runtime main/ISR stack high-water mark under Panchang plus
  nested audio DMA/TIM activity; the static link leaves 668 bytes of RAM.
- [ ] Measure `calc_panchang()` execution time on target.
- [ ] Build or remove the secondary CH32V203C8T configuration according to the
  intended supported targets.

## Post-Integration Peripheral Validation

- [ ] Resolve the confirmed ESP-vs-CH32 loudness gap before further gain edits.
  With the same file and speaker load, measure RMS and peak-to-peak voltage at
  ESP GPIO25 and GPIO26, CH32 PA8 after reconstruction, TLV9061 pin 1 before
  the output capacitor, `AUX_OUT`, and the downstream amplifier input/output.
  Record the amplifier IC/module, supply, load impedance, gain-setting parts,
  and whether the ESP DAC channels are summed or used differentially.
- [ ] Inspect the populated filter capacitor markings. If they are 4.7 uF as
  drawn, replace the IN+ shunt capacitor and both parallel feedback capacitors
  with 4.7 nF parts. Configure the TLV9061 as a unity follower (output directly
  to IN-, remove the IN--to-ground gain resistor) for the calculated 19.95 kHz,
  Q=0.707 baseline.
- [ ] Add and verify a quiet 1.65 V VREF: 10 kOhm/10 kOhm divider, 100 nF plus
  10 uF decoupling, approximately 100 kOhm IN+-to-VREF bias, and the filter
  shunt capacitor returned to VREF. Confirm idle IN+ and OUT are approximately
  1.65 V before reconnecting the external amplifier.
- [ ] Flash V10 and confirm the first LCD screen is
  `ENC+MP3 V10 / AUTO GAIN VOL255`; verify boot proceeds directly from
  `ARITH PASS` to `MOUNTING SD` with no RAW PA8 or DMA sine test.
- [ ] Press DOWN and test representative low-level downloaded `.mp3` files:
  confirm significantly louder, clear output at normal speed/pitch, with no
  clipping, distortion, pumping, hiss, or unwanted noise. Record `P:`, `D:`,
  and underflow count; require zero production underflows.
- [ ] Test short spoken/bell clips specifically. Confirm the new 32x initial
  envelope makes the first syllable/tone clearly audible and that the
  block-look-ahead reduction prevents overload when a file starts loudly.
- [ ] Press UP and test the selected ENC through the shared bounded gain path.
  Confirm louder quiet passages without clipping, distortion, pumping, hiss,
  speed/pitch changes, decryption/decoding errors, or nonzero production
  underflows. Record final metadata/counters.
- [ ] Exercise V10 error handling with a missing folder, empty folder, wrong-key
  `.enc`, truncated ID3/file, unsupported codec/stereo/rate, oversized frame,
  mid-stream format change, SD read interruption, and forced DMA timeout.
- [ ] Measure the V10 PA8 carrier near 375 kHz and the 32 kHz sample-update
  timing during file playback. Measure a representative 44.1 kHz asset
  before accepting the fractional ARR clock path.
- [ ] Inspect the actual TLV9061 PCB/BOM: record whether both parallel feedback
  capacitors are populated, confirm whether all three filter values are 4.7 uF
  or 4.7 nF, and photograph/measure their markings.
- [ ] Locate or confirm the absence of the 1.65 V analog reference. Measure DC
  at TLV9061 pins 3 (IN+), 4 (IN-), and 1 (OUT) with idle PWM duty 128.
- [ ] Scope PA8/AUX and TLV9061 OUT during representative MP3 playback. Record
  PWM carrier, filtered amplitude, DC bias, rail clipping,
  ringing/oscillation, and `AUX_OUT` amplitude.
- [ ] Document the actual downstream amplifier/speaker connected to `AUX_OUT`;
  the TLV9061 is a signal-conditioning op amp, not the speaker power stage.
- [ ] Add/check a runtime high-water guard during repeated MP3 playback and
  full schedule/Panchang execution; the stack is now 2,048 bytes, but interrupt
  nesting is not measured on hardware.
- [ ] Reflash the standalone diagnostic and revalidate `TEST.TXT` first-page,
  UP/DOWN paging, MENU exit/reopen, and missing/empty/open/read-error screens
  after the bare-metal key-wait correction.
- [ ] Revalidate RTC detection, read/write, scheduling use, and persistence in
  the merged cooperative application, including the light service's independent
  one-second reads during menu waits and audio DMA waits.
- [ ] Revalidate SD/FatFs access with `settings.txt`, `playlist.txt`,
  `holiday.txt`, `menu.txt`, `festival.txt`, `special.txt`, and audio assets.
- [ ] Confirm `RLY_IN`/`LGT_IN` active-level polarity against the PCB stages.
- [ ] Characterize the corrected AUX/TLV9061 filter across required sample
  rates and confirm adequate PWM-carrier rejection.
- [ ] At the new maximum digital level, scope PA8, the TLV9061 output before
  the coupling capacitor, and `AUX_OUT`; verify no flat-topping or bias/swing
  violation. Measure downstream amplifier supply current and amplifier/speaker
  temperature during a sustained worst-case asset. Reduce the digital target
  if any hardware limit or audible distortion is observed.
- [ ] Compare ESP DAC and CH32 `AUX_OUT` RMS voltage with the same decoded file
  and load. The ESP enables both internal DAC channels while CH32 has one PA8
  PWM output; document how the external amplifier is connected before
  attributing any remaining level difference to software.

## Functional Testing

- [ ] Verify the internal-flash config store on target, including power-loss
  persistence, slot rotation, corrupt-newest fallback, and writes during audio.
- [ ] Test `settings.txt` parsing including all supported timezone formats,
  the exact `HappyBell 2025 - ` welcome prefix, and ignored extra lines.
- [ ] Test holiday skip, playlist types `1`/`2`/`3`, every supported sequence
  token, group rotation/wrap, and trigger-window power-loss resume.
- [ ] Compare Panchang output with `C:\OfficeWorks\esp_bell_idf` for known
  dates, including Tamil solar-month rollover at sunset, and verify
  festival/special-day matching.
- [ ] Exercise every menu screen, verify the correct config-store locations,
  confirm `menu.txt` labels retain their original case, and verify that
  date/time editors show the reference CGRAM slot-2 cursor glyph.
- [ ] Verify `.enc` playback matches the equivalent `.mp3`.
- [ ] Re-run the host PCM comparison after deployed-profile specialization,
  covering the actual mono MPEG-1 Layer III 32-kHz 64/128-kbps corpus,
  padding, CRC-protected headers if present, ID3v2, plain MP3, and decrypted
  ENC input. The asset files were unavailable during the final clean build.
- [ ] On hardware, verify representative transition-boundary announcements.
  Host comparison found maximum tithi/nakshatra end-time differences below two
  minutes, but five-minute spoken rounding differed in 57/41 of 612 monthly
  cases; confirm the product tolerance before release.
- [ ] Validate PA8 audio carrier/sample timing, `AUX_OUT`, stop behavior, and
  repeated playback; require zero underflows for production assets and resolve
  any residual granule decode-time gap.
- [ ] Test light scheduling for normal and midnight-spanning windows.

## System Integration

- [ ] Breadboard the final LM358-plus-passives stage shown in
  `LM358_AUX_OUT_gain_only.svg` and validate it into a load of 10 kOhm or
  greater. Do not connect the passive speaker directly to this output.
- [ ] Breadboard and qualify the LM358B-only external amplifier shown in
  `LM358_only_discrete_speaker_amplifier.svg`: begin with a 100 mA supply
  current limit and no speaker, verify all DC nodes, then test an 8-ohm dummy
  load before the speaker and record clipping, temperature, and supply current.
- [ ] Remove the direct `AUX_OUT`-to-passive-speaker connection. Add a
  PAM8302A mono analog-input Class-D stage (or electrically equivalent), power
  it from a verified 5 V rail, locally decouple it with 1 uF and 10 uF, feed
  it from the AC-coupled `AUX_OUT`, and connect the speaker only across the
  amplifier's differential outputs.
  This is electrically required but presently blocked by the owner's
  no-new-components/no-PCB-change constraint.
- [ ] Replace the three 4.7 uF filter capacitors with 4.7 nF parts, change the
  TLV9061 output-to-IN- 1.2 kOhm resistor to 0 ohm, remove the IN--to-ground
  1.2 kOhm resistor, and add the documented decoupled 1.65 V input bias.
- [ ] Run a full scheduled bell/announcement day including Panchang playback
  and a holiday-skip day.
- [ ] Document and verify the final UART terminal setup and whether RX is used.
- [ ] Perform long-duration stability and repeated-playback testing.
- [ ] Delete `_to_delete/` after the removed legacy PWM source is confirmed no
  longer required.
- [ ] Resolve remaining hardware and software `TBD` items needed for release.
