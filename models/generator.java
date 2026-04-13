import java.util.*;

public class generator {

    private final int MIN_N	    = 1;
    private final int MAX_N	    = 100000;
    private final int MIN_M	    = 1;
    private final int MAX_M     = 30;
    private final int MIN_TYPES	= 1;
    private final int MAX_TYPES	= 200;
    private final int MIN_USERS	= 1;
    private final int MAX_USERS	= 10000;
    private final int MIN_URGNT	= 0;
    private final int MAX_URGNT	= 3;
    private final int MIN_T	    = 1;
    private final int MAX_T	    = 2000;
    private final int MIN_C	    = 1;
    private final int MAX_C	    = 2147483647;

    private int n;
    private int m;
    private int c;
    private int[][] tasks_data;
    
    private Random random;

    private int randomIntBetween(int lower, int upper) {
        return lower + random.nextInt(upper - lower + 1);
    }

    private double randomDoubleBetween(double lower, double upper) {
        return lower + random.nextDouble() * (upper - lower);
    }

    private void shuffle(int[] array) {
		for (int i = 0; i < array.length; ++i) {
			int randomIndexToSwap = random.nextInt(array.length);
			int temp = array[randomIndexToSwap];
			array[randomIndexToSwap] = array[i];
			array[i] = temp;
		}
    }

    private void generate(long seed) {
        if (seed == 1) { // sample case
            n = 5;
            m = 2;
            c = 9;
            tasks_data = new int[][] {
                {4, 1, 2, 6},
                {7, 2, 3, 1},
                {4, 3, 3, 4},
                {7, 1, 1, 8},
                {4, 2, 2, 7}
            };
            return;
        }
        random = new Random(seed);
        int types, users;
        do {
            n = randomIntBetween(MIN_N, MAX_N);
            users = randomIntBetween(MIN_USERS, MAX_USERS);
            types = randomIntBetween(MIN_TYPES, MAX_TYPES);        
        } while(types * users < n);
        m = randomIntBetween(MIN_M, MAX_M);
        c = randomIntBetween(MIN_C, MAX_C);
        double avgT = randomDoubleBetween(MIN_T, MAX_T);
        double urgent = randomDoubleBetween(MIN_URGNT, MAX_URGNT);
        int[] tasks = new int[types * users];
        for(int i = 0; i < tasks.length; ++i) {
            tasks[i] = i;
        }
        shuffle(tasks);
        double[] excTimeList = new double[n];
        double scale = Math.min(avgT, MAX_T - avgT);
        for(int i = 0; i < excTimeList.length; ++i) {
            excTimeList[i] = random.nextGaussian()*scale + avgT;
        }
        tasks_data = new int[n][4];
        for(int i = 0; i < tasks_data.length; ++i) {
            int excTime = (int)(excTimeList[i]);
            excTime = Math.max(excTime, MIN_T);
            excTime = Math.min(excTime, MAX_T);
            tasks_data[i][0] = tasks[i] % types + 1;
            tasks_data[i][1] = tasks[i] / types + 1;
            tasks_data[i][2] = excTime;
            tasks_data[i][3] = (int)(avgT * (i + 1) / m * urgent + avgT * 3);
        }
    }

    private void print() {
        System.out.println("" + n + " " + m + " " + c);
        for (int i = 0; i < tasks_data.length; ++i) {
            for(int j = 0; j < tasks_data[i].length; ++j) {
                if(j != 0) {
                    System.out.print(' ');
                }
                System.out.print(tasks_data[i][j]);
            }
            System.out.println();
        }
    }

    public static void main(String args[]) {
        long seed = 1L;
        if (args.length == 1) seed = Long.parseLong(args[0]);
        generator g = new generator();
        g.generate(seed);
        g.print();
    }
}
