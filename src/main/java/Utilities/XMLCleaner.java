package Utilities;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class XMLCleaner {

    public static void XMLCleaner(String inputFile, String outputFile) throws IOException {

        Path originalFileName = Path.of(inputFile);
        Path intermFileName = Path.of(outputFile);

        String actual = Files.readString(originalFileName);

        String content = actual.replace("xmlns=\"http://www.loc.gov/MARC21/slim\"\n" +
                "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n" +
                "xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim\n" +
                "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\"", "");


        //System.out.println(content);
        Files.writeString(intermFileName, content);
        int ok1 = 1;

    }

}
