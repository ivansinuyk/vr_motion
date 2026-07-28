# Article 2 - consolidated tables

## table1_dataset_subset

            Characteristic                                Full dataset                        Annotated subset
               Sessions, n                                          71                                      25
          Camera viewpoint    down-the-line: 59; face-on: 10; other: 2 down-the-line: 21; face-on: 3; other: 1
       Capture speed class regular: 47; slow: 23; super slow motion: 1                    regular: 17; slow: 8
    Frame-rate bucket, fps                          31–60: 41; ≤30: 30                       31–60: 18; ≤30: 7
         Resolution bucket     ≥1080 p: 43; <720 p: 14; 720–1080 p: 14   ≥1080 p: 17; 720–1080 p: 5; <720 p: 3
             Quality grade         medium: 47; good: 12; difficult: 12       medium: 17; difficult: 4; good: 4
                 Club type           driver: 32; iron: 23; unknown: 16         driver: 12; iron: 7; unknown: 6
Clubhead control points, n                                           -                    260 (in 25 sessions)

## table2_annotation_protocol

               Event                         Visual criterion                           Role
             Address        Last stable frame before takeaway         Time-origin diagnostic
    Top of backswing Maximal backswing extent before reversal Compared with transition proxy
Downswing transition     First sustained motion toward impact Compared with transition proxy
              Impact    Closest visible clubhead-ball contact  Compared with impact detector

## table3_event_timing

          Auto / manual  n  Median |error|, frames Median |error|, ms (95% CI)
       Transition / top 25                      43              920 (760–1835)
Transition / transition 25                      46             1000 (820–1902)
        Impact / impact 25                      42               817 (660–960)

## table4_trajectory_error

         Phase n_s / n_p Median, % diag. (95% CI)   P95 / max, px
     Backswing    25/105         0.67 (0.56–0.96)    45.5 / 104.3
    Transition       5/5        0.87 (0.18–11.64)   124.7 / 144.2
     Downswing     24/44         0.67 (0.51–0.98) 1589.1 / 2185.5
 Impact region     24/59         0.88 (0.80–1.97)  237.9 / 2473.0
Follow-through     24/47         0.92 (0.72–1.47)  706.5 / 1434.1
    All phases    25/260         0.82 (0.69–0.90)  265.6 / 2473.0

## table5_sensitivity

                  Metric  Median Δsym, %  Worst, %  Median ρ
        Smoothness index            10.0      20.9      0.63
         Path efficiency            14.2      46.5      0.61
           Maximum speed            24.2      83.6      0.50
    Maximum acceleration            48.9      94.2      0.43
Maximum angular velocity            25.5      95.6      0.79
           Curvature RMS            39.8     174.6      0.89
             Swing tempo            75.4     166.6      0.24
    Backswing peak speed            53.9     192.3      0.44

## table6_ablation

                   Stage  Δpoints, n  Δraw, cm RMS jerk, m/s^3
           Raw landmarks           0       0.0           17334
             Median only         143      15.3           14448
             Kalman only         157       9.4             881
            Kalman + RTS         162     170.2            0.43
Kalman + RTS + despiking           0     170.2            0.43
           Full pipeline         162       2.3           11871

## table7_robustness_ranking

                  Metric  Median symmetric |change|, % Scenarios low/moderate/high                Interpretation
        Smoothness index                          10.0                       6/6/0                Candidate only
         Path efficiency                          14.2                       6/3/3           Condition-dependent
           Maximum speed                          24.2                       4/2/6 High perturbation sensitivity
Maximum angular velocity                          25.5                       5/1/6 High perturbation sensitivity
           Curvature RMS                          39.8                       4/1/7 High perturbation sensitivity
    Maximum acceleration                          48.9                       4/1/7 High perturbation sensitivity
    Backswing peak speed                          53.9                       3/2/7 High perturbation sensitivity
             Swing tempo                          75.4                       4/0/8 High perturbation sensitivity
