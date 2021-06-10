Python implementation of Minimal Generalization rule learner (Albright & Hayes 2002, 2003)

* Currently implemented only up through A&H (2002, section 3.2)  
    - Minimal generalization of rules with shared change  
    - Rule reliability and lower confidence limit

Modifications of strict MinGen not yet implemented

* 3.3 Improving confidence with phonology  
    - Broaden rules by learning phonological rules to fix misapplication

* 3.4 Overcoming complementary distribution  
    - Generalize further by forming cross-context rules (swap changes of rules with common focus, A -> B / C __ D and A -> B' / C' __ D')  
    - Learn phonological rules to fix misapplication, as above

* 3.7 Impugnment as a solution to the distributional encroachment problem  
    - Comparison of rules related by more-general-than relation  
    - Upper confidence limit
