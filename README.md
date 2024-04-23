## File Structure

Below is the file structure and descriptions of each component in the project:
The whole simulator is located under `Simulator` Folder

- `core/` - The simulator itself, including the LLC, CPU, GPU, and SYSTEM components.
- `header/` - Header files used within the Simulator.
- `Test/` - Unit tests for each module within the Simulator.
- `Testcase/` - Test cases for the entire system and scripts to analyze the results.
- `top/` - Python scripts to run the simulator. Configuration settings can be adjusted in `Top.py`.
- `utility/` - Contains all the primitives used for the simulator and the debug class.

## Running the Simulation

To run the simulation, follow these steps:

1. **Execute the Test**
   - Run the command below in your terminal. This will execute the simulation and save the output to `output.txt`.
     ```bash
     cd Simulator
     python3 -m top.Top > output.txt
     ```

## Configuring Test Cases

To change the test case you want to run, you need to modify the `main` function in the `top/Top.py` file.

### Example

- If you want to run test 6, change the `main` function to `main_test6()`. Here’s how you can do it:

  1. Open `top/Top.py` in your favorite text editor.
  2. Locate the `main` function.
  3. Replace the existing `main` function call with `main_test6()`.
