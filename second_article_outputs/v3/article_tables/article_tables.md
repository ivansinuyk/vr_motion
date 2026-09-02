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
Clubhead control points, n                                           -                    150 (in 25 sessions)

## table2_annotation_protocol

               Event                         Visual criterion                           Role
             Address        Last stable frame before takeaway         Time-origin diagnostic
    Top of backswing Maximal backswing extent before reversal Compared with transition proxy
Downswing transition     First sustained motion toward impact Compared with transition proxy
              Impact    Closest visible clubhead-ball contact  Compared with impact detector

## table3_event_timing

          Auto / manual  n  Median |error|, frames Median |error|, ms (95% CI)
       Transition / top 25                      38              780 (700–1635)
Transition / transition 25                      40              940 (660–1919)
        Impact / impact 25                      40              800 (660–1022)

## table4_trajectory_error

         Phase n_s / n_p Median, % diag. (95% CI)  P95 / max, px
     Backswing     25/60         1.94 (1.69–2.26)   89.8 / 120.8
    Transition       8/8         3.25 (2.08–4.53)    94.7 / 98.9
     Downswing     17/26         3.32 (2.20–3.92)  105.3 / 397.3
 Impact region     16/23         2.70 (1.68–6.38) 361.8 / 2103.0
Follow-through     22/33         2.66 (1.61–3.76) 498.3 / 2492.9
    All phases    25/150         2.54 (1.98–2.88) 169.1 / 2492.9

## table5_sensitivity

                  Metric  Median Δsym, %  Worst, %  Median ρ
        Smoothness index             6.2      15.1      0.73
         Path efficiency             5.9      24.8      0.63
           Maximum speed            18.7      60.8      0.56
    Maximum acceleration            26.0      93.5      0.46
Maximum angular velocity            17.0      89.9      0.81
           Curvature RMS            39.6     157.4      0.93
             Swing tempo            74.4     160.7      0.34
    Backswing peak speed            53.6     179.8      0.44

## table6_ablation

                   Stage  Δpoints, n  Δraw, cm RMS jerk, m/s^3
           Raw landmarks           0       0.0           17334
             Median only         143      15.3           14448
             Kalman only         157       9.4             881
            Kalman + RTS         162     141.4             181
Kalman + RTS + despiking           0     141.4             181
           Full pipeline         162       1.9           11835

## table7_robustness_ranking

                  Metric  Median symmetric |change|, % Scenarios low/moderate/high                Interpretation
         Path efficiency                           5.9                       7/5/0                Candidate only
        Smoothness index                           6.2                       7/5/0                Candidate only
Maximum angular velocity                          17.0                       6/0/6 High perturbation sensitivity
           Maximum speed                          18.7                       5/1/6 High perturbation sensitivity
    Maximum acceleration                          26.0                       4/2/6 High perturbation sensitivity
           Curvature RMS                          39.6                       4/1/7 High perturbation sensitivity
    Backswing peak speed                          53.6                       4/1/7 High perturbation sensitivity
             Swing tempo                          74.4                       4/0/8 High perturbation sensitivity
