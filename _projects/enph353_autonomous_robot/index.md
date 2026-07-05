---
layout: post
title: Autonomous Clue-Finding Simulated Robot
description: This was the final project for ENPH 353, where my partner and I built an autonomous ROS/Gazebo robot to drive through a simulated course, obey traffic constraints, avoid NPCs, read clue boards, and solve a murder mystery without external input once the run started.
skills:
  - ROS / Gazebo
  - Python
  - OpenCV image processing
  - CNN training and deployment
  - Imitation learning exploration
  - State-machine control
  - Debugging simulated robotic systems
  - Data generation and model evaluation

main-image: competition_surface.png
---

# Project Design

ENPH 353 was structured around a simulated autonomous robotics competition. The robot had to drive around a Gazebo course, avoid obstacles and NPCs, obey the important traffic constraints, read clue boards placed around the course, and use those clues to solve a murder mystery. At a higher level, this split the project into two coupled but conceptually separate problems: driving reliably through the map, and reading signs accurately enough that the robot could make the correct final guess.

![Competition surface]({{ page.url | remove: 'index/' | append: 'competition_surface.png' | relative_url }})

The natural temptation in a project like this is to look for one clean end-to-end solution: feed camera images into a model, output motor commands and clue guesses, and hope the system learns everything. In practice, and especially under course time constraints, I think the more useful way to approach the problem was to break it into smaller transformations that could each be tested. The front camera should extract driving features. The side cameras should find candidate signs. A sign crop should be unskewed into a clean rectangular image. That image should become ordered character crops. The character crops should become strings. Finally, those strings should become a valid clue/value pair published to the score tracker.

The final software architecture reflected this separation. `line_follow.py` processed the front camera feed and published driving features, `drive.py` used those features in a state machine to publish `/cmd_vel`, and `plate_detect.py` processed the left and right camera feeds to publish clue guesses to `/score_tracker`. For the last section of the course, `drive_hill.py` used a lightweight CNN to directly choose a driving action from the camera feed.

![Software architecture]({{ page.url | remove: 'index/' | append: 'software_architecture.png' | relative_url }})

My main responsibility was the sign detection and recognition pipeline, while Justin focused primarily on driving. I also explored some of the driving/modeling ideas for the final course section, especially around imitation learning and data collection.

# Driving by exploiting the structure of the course

For the first three sections of the course, we used hand-designed image processing rather than a learned driving policy. The practical reason was speed and transparency: if a line, road edge, bridge, pedestrian, truck, or Baby Yoda had a distinctive colour signature, then binary masks gave us a very fast and debuggable representation of the scene.

![Driving masks]({{ page.url | remove: 'index/' | append: 'driving_masks.png' | relative_url }})

The first section was relatively friendly to this approach because the line had strong contrast against the pavement. The second section was noisier, so the mask needed some preprocessing: blur, threshold, and a morphological cleanup to remove small patches of noise. At this stage the driving problem became less like “understand the road” and more like “decide what the geometry of this white mask is trying to tell us.”

The state machine mostly operated from simple geometric observations. If the line appeared lower on one side of the image, that meant it was closer on that side, so the robot should turn away from it. If the line appeared roughly balanced, the robot could move forward. This was not elegant in the sense of control theory, but it was easy to reason about, which was a real advantage when debugging in simulation.

The bridge required a small change in philosophy. Instead of following the line, the robot watched the water mask and turned away from whichever side the water was approaching. After the bridge, the robot used the visible pink line to transition toward the next part of the course.

NPC handling was also mostly done with masks. The pedestrian’s pants had a consistent enough colour that we could stop at the crosswalk when they were detected in the center of the image. The truck could be thresholded by its characteristic grayscale values, and Baby Yoda could be followed by separate green and gray masks depending on which side of him the robot saw.

![NPC masks]({{ page.url | remove: 'index/' | append: 'npc_masks.png' | relative_url }})

This worked surprisingly well, but the weakness of this approach was exactly what you would expect: edge cases. Once the state machine grew to include special cases for the crosswalk, loop entry and exit, truck following, bridge exit, and offroad section transitions, the simple logic became less simple. Small timing assumptions could interact in hard-to-predict ways, and a special case that fixed one run could quietly break another.

# Using a small CNN where the hand-built masks stopped being enough

The final hill section had much less stable pixel structure. The texture changed, the road boundaries were less clean, and the artisanal mask approach became much less attractive. For this section, we used a lightweight CNN trained from the robot camera feed.

![Sample hill CNN input]({{ page.url | remove: 'index/' | append: 'hill_cnn_input.png' | relative_url }})

The input image was still deliberately simple. We took the blue channel from the 320x320 camera image and kept only the bottom part of the frame, since that was where the driving-relevant information lived. The model output one of five states: `FWD`, `FWD_LEFT`, `LEFT`, `RIGHT`, or `STOP`. This is a nice middle ground between a fully continuous steering model and a giant hand-coded state machine: the CNN learned from images, but the output space was still small enough to reason about.

The model itself was also deliberately lightweight: four convolutional layers with max pooling, batch normalization, and dropout, followed by global average pooling and a dense layer. This gave us a model with about 115k parameters, which was small enough to run comfortably in our ROS/Gazebo setup.

![Driving CNN train and validation loss]({{ page.url | remove: 'index/' | append: 'driving_cnn_loss.png' | relative_url }})

The most useful part of training was not just collecting one dataset and hoping it worked. The actual error analysis was watching the robot drive. If it failed at a specific location, we added more examples there. If it cut a corner too tightly and went offroad, we added examples where it cut less aggressively. That feedback loop felt very similar to the debugging pattern from the rest of the project: isolate a failure mode, collect a targeted correction, test again.

# Reading clue boards without constraining the driving path

My main part of the project was the plate detection and recognition system. The most important design constraint was that sign reading should be as passive as possible. I did not want driving to have to stop directly in front of a sign, line up perfectly, or satisfy too many extra assumptions just so the perception pipeline could work.

To decouple sign reading from the exact driving path, we added two extra cameras to the URDF, angled left and right from the robot centerline. The front camera was still used for driving, while the side cameras gave much cleaner views of clue boards as the robot passed them.

![Side camera views]({{ page.url | remove: 'index/' | append: 'side_camera_views.png' | relative_url }})

The first step was detecting whether a clue board was present and close enough to process. Since every clue board had the same blue border, I made a mask for that blue border and watched for large enough connected components. Pixel count alone was not sufficient, because the back of a farther plate could sometimes produce a misleading number of blue pixels. The more reliable condition was a clean four-sided polygon with enough area, found using OpenCV contour detection and polygon approximation.

Once a plausible board was found, the key operation was an inverse perspective transform. This took the skewed quadrilateral from the camera image and transformed it into a rectangular, front-facing crop. Then the same basic idea was applied again inside the clue board: find the gray text background, unskew it, and produce a consistent image for text extraction.

![Plate extraction pipeline]({{ page.url | remove: 'index/' | append: 'plate_pipeline.png' | relative_url }})

I like this part of the project because it is very bottom-up. The CNN was only asked to solve the part of the problem that really needed learning: classifying a clean 32x32 character image. Everything before that was geometry and image processing: find the border, unskew the board, find the text region, unskew again, threshold the text, split it into characters, and order the characters into words.

# Making character extraction robust

The hardest part of the sign pipeline was not training the character CNN; it was getting clean character crops consistently. Hardcoded character boxes were tempting because the clue boards were generated in a mostly consistent format, but this broke too easily. Small perspective errors accumulated across a word, and eventually a crop would contain part of the next character.

Instead, I used contour finding to isolate connected character regions. If the contour was too small, it could be padded up to a 32x32 character image. If the text was too blurry, several characters could merge into one contour. If the threshold was too aggressive, a single character could fray into disconnected pieces. The solution was to adjust the mask recursively: strengthen the mask when characters blurred together, weaken it when characters fragmented, and split unusually wide contours according to an expected monospace character width.

![Text mask weakening]({{ page.url | remove: 'index/' | append: 'text_mask_weakening.png' | relative_url }})

Finally, I ordered characters by their top-left positions. Characters in the upper half of the text image belonged to the clue category, and characters in the lower half belonged to the clue value. Within each line, sorting horizontally gave the word order, and unusually large gaps between successive characters were used to infer spaces.

The character CNN was intentionally small: three convolution layers with max pooling, then a dense layer and a 36-class output for letters and digits. To generate training data, we modified the competition plate generation code so that clue board characters were randomized, teleported the robot around the clue board positions, ran the extraction pipeline, and wrote the labelled characters to a training directory. That made it possible to collect thousands of realistic character images in minutes, which was much more valuable than hand-building a tiny clean dataset.

![Character distribution]({{ page.url | remove: 'index/' | append: 'character_distribution.png' | relative_url }})

![Character CNN train and validation loss]({{ page.url | remove: 'index/' | append: 'character_cnn_loss.png' | relative_url }})

After training, the model was pruned and quantized, reducing its size by about a factor of ten and giving inference times around 0.1 ms, which was far faster than the rest of the pipeline needed.

![Model size comparison]({{ page.url | remove: 'index/' | append: 'model_size_comparison.png' | relative_url }})

One nice final trick was using the structure of the mystery itself. Even if the CNN slightly misread the clue category, the set of valid clue categories was known. So instead of trusting the category string directly, we matched it to the valid category with the smallest Hamming distance. This meant that a near miss like one wrong character did not necessarily become a wrong score tracker message.

# Video demonstrations

Below is a video showing the performance of the robot in an isolated run. In it you can see all aspects of our design at play to achieve a perfect run in practice!

<div class="video-container">
  <video class="post-video" controls muted playsinline preload="metadata" poster="{{ page.url | remove: 'index/' | append: 'competition_surface.png' | relative_url }}">
    <source src="{{ page.url | remove: 'index/' | append: 'expected_run_4.mp4' | relative_url }}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>

# Results and Lessons Learned

In competition, driving worked at the start, but an unresolved truck edge case caused the robot to follow the truck in loops until our preset timer expired. During that run, all signs were detected, though two were slightly misread due to similar-looking characters. Outside the competition run, we recorded four consecutive expected-performance runs averaging 41 points, with the best run scoring about 50 points before accounting for a forgotten respawn penalty.

I think the most important lesson from this project is that transparency matters enormously. The state-machine driving approach was attractive because every decision was explainable, but as the number of edge cases grew, it became harder to keep globally reliable. The CNN approach was less transparent internally, but the training/debugging cycle was actually simpler in some ways: watch failure, add targeted data, retrain, and test again.

For the plate reading pipeline, I was happy with the bottom-up structure. The system did not ask one model to solve the whole problem. Instead, classical image processing handled the geometry, contour logic handled character extraction, a small CNN handled character classification, and a final string-matching layer used the known structure of the clue set. That decomposition made the system much easier to debug and much faster to run.

If I were to do this again, I would start imitation learning earlier and treat the state machine as a baseline rather than the central driving strategy. I would also put more effort into transparent CNN evaluation from the start: richer validation examples, more targeted augmentation, and scripts that collect difficult examples passively while the robot drives. That would have made the final integration less dependent on late hardcoded threshold tuning.

## Final Report

For more detailed discussion of the driving state machine, plate detection pipeline, CNN architectures, competition performance, and methods we tried but did not adopt, see the [final report]({{ page.url | remove: 'index/' | append: 'final_report.pdf' | relative_url }}).
