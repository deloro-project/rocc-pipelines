package BARtoROCC;




import BARObject.Collection;
import BARObject.Datafield;
import Objects.barOutObject;
import Objects.subFieldObject;
import Utilities.XMLCleaner.*;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Unmarshaller;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import static Utilities.XMLCleaner.XMLCleaner;

public class Main {
    public static void main(String[] args) throws JAXBException, IOException {


        String originalFolderPath = "original//";
        String inputFolderPath = "input//";


        File origFolder = new File(originalFolderPath);
        File[] listOfOrigFiles = origFolder.listFiles();

        for (File file : listOfOrigFiles) {
            if (file.isFile()) {
                XMLCleaner(originalFolderPath+"//"+file.getName(), inputFolderPath + "//" +file.getName());
                System.out.println(file.getName());
            }
        }

        int ok1 = 1;

        File inputFolder = new File(inputFolderPath);
        File[] listOfInputFiles = inputFolder.listFiles();

        ArrayList<barOutObject> myInputBarList = new ArrayList<>();

        for (File file : listOfInputFiles) {
            if (file.isFile()) {

                JAXBContext context = JAXBContext.newInstance(Collection.class);
                Unmarshaller unMarshaller = context.createUnmarshaller();
                Collection barInput = (Collection) unMarshaller.unmarshal(new FileInputStream(inputFolderPath+ "//"+file.getName()));

                for (int i = 0; i < barInput.getRecord().getDatafield().size(); i ++){
                    ArrayList<subFieldObject> mySubFieldList = new ArrayList<>();
                    for (int j = 0; j < barInput.getRecord().getDatafield().get(i).getSubfield().size();j++){
                        mySubFieldList.add(new subFieldObject(
                                barInput.getRecord().getDatafield().get(i).getSubfield().get(j).getCode(),
                                barInput.getRecord().getDatafield().get(i).getSubfield().get(j).getContent()
                        ));
                    }
                    myInputBarList.add(new barOutObject(
                            barInput.getRecord().getDatafield().get(i).getTag(),
                            barInput.getRecord().getDatafield().get(i).getInd1(),
                            barInput.getRecord().getDatafield().get(i).getInd2(),
                            mySubFieldList));
                }
            }
        }
        int ok =1;

    }


}
